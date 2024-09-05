import asyncio
import logging
from fastapi import  HTTPException, Request

import src.logging_config

from src.service.power_code import PowerBuddy

logger = logging.getLogger(__name__)

class MistBuddyManager:
    def __init__(self):

    async def start_mistbuddy(self, host_ip: str, tent_name: str, duration_on: float):
        await self.stop_mistbuddy()  # Stop any running misting, just in case
        try:
            self.power_instance = PowerBuddy(tent_name, host_ip)
            self.mist(True, duration_on=5)
            # Start the timer to run turn_on_power_task every 60 seconds

        except ValueError as exc:
            logger.error("Value error in start_mistbuddy", exc_info=True)
            raise HTTPException(status_code=400, detail="Invalid input parameters") from exc
        except asyncio.CancelledError as exc:
            logger.info("Misting operation cancelled")
            await self.stop_mistbuddy()
            raise HTTPException(status_code=400, detail='Invalid input parameters') from exc

        except Exception as exc:
            logger.error("Unexpected error in start_mistbuddy", exc_info=True)
            await self.stop_mistbuddy()
            raise HTTPException(status_code=500, detail="Error starting MistBuddy") from exc
        logger.info("MistBuddy started successfully.  Will spew mist every %s seconds each minute.", duration_on)

    def mist(self, on: bool, duration_on):
        try:
            while on is True and self.power_instance is not None:
                self.power_instance.power_on(duration_on)
                asyncio.sleep()
        except asyncio.CancelledError:
            logger.info("Misting operation cancelled")
            raise HTTPException(status_code=400, detail='Misting operation cancelled')

    async def stop_mistbuddy(self):
        self.mist(False)
        self.power_instance = None

        logger.info("MistBuddy stopped successfully.")

_mistbuddy_manager = None
def get_mistbuddy_manager() -> MistBuddyManager:
    global _mistbuddy_manager
    if not _mistbuddy_manager:
        return MistBuddyManager()
    return _mistbuddy_manager
