import asyncio
import logging
from fastapi import HTTPException
from pydantic import AnyHttpUrl, IPvAnyAddress
from pydantic_settings import BaseSettings

import src.logging_config
from src.config import settings, get_host_ip
from src.service.power_code import PowerBuddy


logger = logging.getLogger(__name__)

class MistBuddyManager:
    def __init__(self):
        self.stop_event: asyncio.Event | None = None
        self.timer_task: asyncio.Task | None = None
        self.power_instance: PowerBuddy | None = None

    async def start_mistbuddy(self, tent_name: str, duration_on: float):
        await self.stop_mistbuddy()  # Stop any running misting, just in case
        try:
            self.power_instance = PowerBuddy(tent_name, get_host_ip)
            # Start the timer to run turn_on_power_task every 60 seconds
            self.stop_event = asyncio.Event()
            self.timer_task = asyncio.create_task(self.power_instance.async_timer(60, self.stop_event, duration_on))
        except ValueError:
            logger.error("Value error in start_mistbuddy", exc_info=True)
            raise HTTPException(status_code=400, detail="Invalid input parameters")
        except asyncio.CancelledError:
            logger.info("Misting operation cancelled")
            await self.stop_mistbuddy()
        except Exception:
            logger.error("Unexpected error in start_mistbuddy", exc_info=True)
            await self.stop_mistbuddy()
            raise HTTPException(status_code=500, detail="Error starting MistBuddy")
        logger.info(f"MistBuddy started successfully.  Will spew mist every {duration_on} seconds each minute.")

    async def stop_mistbuddy(self):
        global mistbuddy_manager
        if self.timer_task:
            self.timer_task.cancel()
            try:
                await self.timer_task
            except asyncio.CancelledError:
                pass
        if self.power_instance:
            await self.power_instance.stop()

        if self.stop_event:
            self.stop_event.set()

        self.timer_task = None
        self.power_instance = None
        self.stop_event = None

        mistbuddy_manager = None
        logger.info("MistBuddy stopped successfully.")

mistbuddy_manager = None
def get_mistbuddy_manager():
    global mistbuddy_manager
    if mistbuddy_manager is None:
        mistbuddy_manager = MistBuddyManager()
    return mistbuddy_manager