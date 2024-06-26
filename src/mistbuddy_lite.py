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
from settings_model import SettingsModel, Settings

logger = LoggerBase.setup_logger("MistBuddyLite", logging.DEBUG)

app = FastAPI()

# Define the Pydantic model with validation constraints
class MistbuddyLiteForm(BaseModel):
    tent_name: str
    duration_on: confloat(gt=0, le=60)  # duration_on must be > 0 and <= 60

    @field_validator("tent_name")
    def validate_tent_name(cls, value):
        if not Settings.is_valid_tent_name(value):
            raise ValueError(f"Invalid tent name: {value}. Please check the growbuddies_settings file.")
        return value

# Class to encapsulate the state and logic
class MistBuddyManager:
    def __init__(self, settings: SettingsModel):
        self.settings = settings
        self.power_instance = None
        self.stop_event = None
        self.timer_task = None

    async def start_mistbuddy(self, tent_name: str, duration_on: float):
        await self.stop_mistbuddy()  # Stop any running misting, just in case

        try:
            self.power_instance = PowerBuddy(tent_name, self.settings)
        except Exception as e:
            await self.stop_mistbuddy()
            raise HTTPException(status_code=500, detail=f"Error creating PowerBuddy instance. Error: {e}")

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

# Initialize the settings once and pass it to MistBuddyManager
settings = Settings.load()
mistbuddy_manager = MistBuddyManager(settings)

@app.post("/api/v1/mistbuddy-lite/start")
async def mistbuddy_lite_start(form_data: MistbuddyLiteForm = Body(...), manager: MistBuddyManager = Depends(lambda: mistbuddy_manager)):
    await manager.start_mistbuddy(form_data.tent_name, form_data.duration_on)
    return {"status": f"mistbuddy lite spewing mist every {form_data.duration_on} seconds each minute."}

@app.get("/api/v1/mistbuddy-lite/stop")
async def mistbuddy_lite_stop(manager: MistBuddyManager = Depends(lambda: mistbuddy_manager)):
    await manager.stop_mistbuddy()
    return {"status": "stopped misting."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("mistbuddy_lite:app", host="0.0.0.0", port=8080, reload=True)
