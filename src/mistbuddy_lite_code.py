import asyncio
import json
import logging
from json import JSONDecodeError

# I tried to get PYTHONPATH to work from .env, but no luck with
# the GrowBuddies_shared directory. So, I attach it to sys.path.
# sys.path.append('/root/projects/mistBuddy/GrowBuddies_shared')
# from dotenv import load_dotenv
# load_dotenv()


from fastapi import Body, FastAPI, Depends, HTTPException

from logger_code import LoggerBase
from power_code import PowerBuddy
from mistbuddy_lite_state_code import ServicesAddress, MistBuddyLite_state


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

    async def start_mistbuddy(self, mistbuddy_state: MistBuddyLite_state):
        """
        The MistBuddy assigned to name starts spewing mist for duration_on (<60) seconds.  It will repeat every minute until stopped.

        """
        await self.stop_mistbuddy()  # Stop any running misting, just in case


        self.power_instance = PowerBuddy(mistbuddy_state.address, mistbuddy_state.power_messages)
        await self.power_instance.start()

        # Start the timer to run turn_on_power_task every 60 seconds
        self.stop_event = asyncio.Event()
        self.timer_task = asyncio.create_task(self.power_instance.async_timer(60, self.stop_event, mistbuddy_state.duration_on))

    async def stop_mistbuddy(self):
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

@app.post("/api/v1/mistbuddy-lite/start")
async def mistbuddy_lite_start(mistbuddy_state: MistBuddyLite_state = Body(...), mistbuddy_controller: MistBuddyLiteController = Depends(lambda: MistBuddyLiteController.get_mistbuddy_controller())):
    '''
    Start the MistBuddy device to spew out mist for duration_on seconds. The mist spewing repeats every minute until stopped.

    The endpoint expects a POST request with a JSON body that contains the duration_on and name properties of a MistBuddyLite_state object. Pydantic will parse the JSON to provide the mistbuddy_state instance.  The code is dependent on a MistBuddyLiteController instance to control the MistBuddy device. By using Depends, the code provides a singleton instances of the mistbuddy_controller.
    '''
    # Before starting, the ServicesAddress and power messages need to be in the state.
    try:
        settings = MistBuddyLite_state.load_growbuddies_settings('growbuddies_settings.json')
        services_address = ServicesAddress(**settings['global_settings'])
        power_messages = settings['mqtt_power_messages'][mistbuddy_state.name]
    except FileNotFoundError:
        print("growbuddies_settings.json file not found.")
        services_address, power_messages = None, None
    except JSONDecodeError:
        print("Error decoding growbuddies_settings.json. Please check the file format.")
        services_address, power_messages = None, None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        services_address, power_messages = None, None
    if not services_address or not power_messages:
        raise HTTPException(status_code=500, detail="Error loading services_address and power_messages from growbuddies_settings.json")

    mistbuddy_state.power_messages = power_messages
    mistbuddy_state.services_address = services_address

    await mistbuddy_controller.start_mistbuddy(mistbuddy_state)
    return {"status": f"mistbuddy lite spewing mist every {mistbuddy_state.duration_on} seconds each minute to the MistBuddy named {mistbuddy_state.name}."}

@app.get("/api/v1/mistbuddy-lite/stop")
async def mistbuddy_lite_stop(mistbuddy_controller: MistBuddyLiteController = Depends(lambda: MistBuddyLiteController.get_mistbuddy_controller())):
    await mistbuddy_controller.stop_mistbuddy()
    return {"status": "stopped misting."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("mistbuddy_lite:app", host="0.0.0.0", port=8080, reload=True)
