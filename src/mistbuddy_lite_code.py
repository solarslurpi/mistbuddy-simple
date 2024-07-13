import asyncio
import logging


# I tried to get PYTHONPATH to work from .env, but no luck with
# the GrowBuddies_shared directory. So, I attach it to sys.path.
# sys.path.append('/root/projects/mistBuddy/GrowBuddies_shared')
# from dotenv import load_dotenv
# load_dotenv()


from fastapi import Body, FastAPI, Depends

from logger_code import LoggerBase
from power_code import PowerBuddy
from mistbuddy_lite_state_code import  MistBuddyLiteState, MistBuddyLiteStateSingleton, UserInput


logger = LoggerBase.setup_logger("MistBuddyLite", logging.DEBUG)

app = FastAPI()



# Class to encapsulate the state and logic
class MistBuddyLiteController:
    '''Turn on MistBuddy for the specified tent name for duration_on seconds (< 60), repeating every minute.

    NOTE: Prior to running this code, ensure that the Tasmotized power plugs are set up and configured correctly.

    NOTE: The MistBuddy name must be defined within the growbuddies_settings.json file. The name must be unique. It is used to look up the MQTT topics for the MistBuddy device with the given name.

    '''

    _controller_instance = None

    @classmethod
    def get_mistbuddy_controller(cls):
        if cls._controller_instance is None:
            cls._controller_instance = MistBuddyLiteController()
        return cls._controller_instance


    def __init__(self):
        self.power_instance = None
        self.timer_task = None
        self.stop_event = None

    async def start(self, mistbuddy_state: MistBuddyLiteState):
        """
        MistBuddy starts spewing mist for duration_on (<60) seconds.  It will repeat every minute until stopped.
        """
        await self.stop()  # Stop any running misting, just in case.
        self.power_instance = PowerBuddy(mistbuddy_state.address, mistbuddy_state.power_messages)
        self.power_instance.start() # not an async function
        # Start the timer to run turn_on_power_task every 60 seconds
        self.stop_event = asyncio.Event()
        self.timer_task = asyncio.create_task(self.power_instance.async_timer(60, self.stop_event, mistbuddy_state.duration_on))

    async def stop(self):
        '''Stop spewing mist. Cleanup the timer_task, power_instance, and stop_event.'''
        if self.timer_task:
            self.timer_task.cancel()
            try:
                await self.timer_task
            except asyncio.CancelledError:
                pass
        if self.power_instance:
            self.power_instance.stop()
        if self.stop_event:
            self.stop_event.set()
        self.timer_task = None
        self.stop_event = None
        self.power_instance = None


# Define the dependency function to get the MistBuddyLiteState based on user_input
async def get_mistbuddy_state(user_input: UserInput = Body(...)):
    try:
        mistbuddy_state = MistBuddyLiteStateSingleton.get_mistbuddy_state(user_input)
    except Exception as e:
        logger.error(f"Error creating MistBuddyLiteState: {e}")
        raise
    return mistbuddy_state
@app.post("/api/v1/mistbuddy-lite/start")
async def mistbuddy_lite_start(
    user_input: UserInput = Body(...),
    mistbuddy_controller: MistBuddyLiteController = Depends(MistBuddyLiteController.get_mistbuddy_controller),
    mistbuddy_state: MistBuddyLiteState = Depends(get_mistbuddy_state)
):
    '''
    Start the MistBuddy device to spew out mist for duration_on seconds every minute.

    e.g. json input to POST:    {"duration_on: 10.0, "name": "tent_one" }

    - duration_on is a float value between (0.0 < duration_on < 60.0)
    - name is a string value that must match the name in the growbuddies_settings.json file.
    '''

    await mistbuddy_controller.start(mistbuddy_state)
    return {"status": f"mistbuddy lite spewing mist every {mistbuddy_state.duration_on} seconds each minute to the MistBuddy named {mistbuddy_state.name}."}

@app.get("/api/v1/mistbuddy-lite/stop")
async def mistbuddy_lite_stop(mistbuddy_controller: MistBuddyLiteController = Depends(lambda: MistBuddyLiteController.get_mistbuddy_controller())):
    await mistbuddy_controller.stop()
    return {"status": "stopped misting."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("mistbuddy_lite_code:app", host="0.0.0.0", port=8080, reload=True)
