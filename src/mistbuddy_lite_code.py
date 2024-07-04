import asyncio
import logging
import os
import sys
# I tried to get PYTHONPATH to work from .env, but no luck with
# the GrowBuddies_shared directory. So, I attach it to sys.path.
sys.path.append('/root/projects/mistBuddy/GrowBuddies_shared')
# from dotenv import load_dotenv
# load_dotenv()


from fastapi import Body, FastAPI, Depends, HTTPException
from pydantic import BaseModel, confloat, field_validator

from logger_code import LoggerBase
from power_code import PowerBuddy
from mistbuddy_lite_state_old import ServicesAddress, MistBuddyLite_state


logger = LoggerBase.setup_logger("MistBuddyLite", logging.DEBUG)

app = FastAPI()


# Class to encapsulate the state and logic
class MistBuddyLiteController:
    '''Turn on MistBuddy for the specified tent name for duration_on seconds (< 60), repeating every minute.

    NOTE: Prior to running this code, ensure that the Tasmotized power plugs are set up and configured correctly.

    NOTE: The MistBuddy name must be defined within the growbuddies_settings.json file. The name must be unique. It is used to look up the MQTT topics for the MistBuddy device with the given name.

    Attributes:
    settings (SettingsModel): Configuration settings found in growbuddies_settings.json. These settings are shared across GrowBuddies services.
    power_instance: Instance for controlling the power to the MistBuddy device. Initially None.
    '''
    # Hard-coded MQTT power topics.  There didn't seem a reason to make these configurable?
    MQTT_POWER_TOPICS = ["cmnd/mistbuddy_fan/POWER", "cmnd/mistbuddy_mister/POWER"]
    _controller_instance = None

    @classmethod
    def get_mistbuddy_controller(cls):
        if cls._controller_instance is None:
            cls._controller_instance = MistBuddyLiteController()
        return cls._controller_instance

    def __init__(self, name: str = "MistBuddyLite", settings: ServicesAddress = ServicesAddress()):
        # self.services_address = ServicesAddress()
        try:
            self.power_instance = PowerBuddy(name, self.settings)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating PowerBuddy instance. Error: {e}")

        self.state = None
        self.power_instance = None
        self.stop_event = None
        self.timer_task = None

    async def start_mistbuddy(self, name: str, duration_on: float):
        """
        The MistBuddy assigned to name starts spewing mist for duration_on (<60) seconds.  It will repeat every minute until stopped.

        Args:
            name (str): The name of the tent where the MistBuddy device is located.
            duration_on (float): The duration, in seconds, for which the MistBuddy device should mist. This duration should be less than 60 seconds.

        Raises:
            ValueError: If the `duration_on` is not within the expected range.
            ConnectionError: If there is a problem communicating with the MistBuddy device.
        """
        await self.stop_mistbuddy()  # Stop any running misting, just in case



        self.power_instance.start()

        # Start the timer to run turn_on_power_task every 60 seconds
        self.stop_event = asyncio.Event()
        self.timer_task = asyncio.create_task(self.power_instance.async_timer(60, self.stop_event, duration_on))

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
    The endpoint expects a POST request with a JSON body that contains the properties of a MistBuddyLite_state object. Pydantic will parse the JSON to provide the mistbuddy_controller instance.
    '''
    await mistbuddy_controller.start_mistbuddy(mistbuddy_state.name, mistbuddy_state.duration_on)
    return {"status": f"mistbuddy lite spewing mist every {mistbuddy_state.duration_on} seconds each minute to the MistBuddy named {mistbuddy_state.name}."}

@app.get("/api/v1/mistbuddy-lite/stop")
async def mistbuddy_lite_stop(mistbuddy_controller: MistBuddyLiteController = Depends(lambda: MistBuddyLiteController.get_mistbuddy_controller())):
    await mistbuddy_controller.stop_mistbuddy()
    return {"status": "stopped misting."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("mistbuddy_lite:app", host="0.0.0.0", port=8080, reload=True)
