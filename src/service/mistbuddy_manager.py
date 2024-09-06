import asyncio
import logging
from fastapi import  HTTPException, Request

import src.logging_config

from src.service.power_code import PowerBuddy

logger = logging.getLogger(__name__)

class MistBuddyManager:
    def __init__(self):
        self.misting_task: asyncio.Task | None = None
        self.power_instance: PowerBuddy | None = None

    async def start_mistbuddy(self, host_ip: str, tent_name: str, duration_on: float):
        await self.stop_mistbuddy()  # Stop any running misting, just in case
        try:
            self.power_instance = PowerBuddy(tent_name, host_ip)
            self.misting_task = asyncio.create_task(self._misting_cycle(duration_on))
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

    async def _misting_cycle(self, duration_on: float):
        try:
            while True:
                if self.power_instance:
                    self.power_instance.power_on(duration_on)
                await asyncio.sleep(60)  # Wait for a minute before the next cycle
        except asyncio.CancelledError:
            logger.info("Misting cycle cancelled")

    async def stop_mistbuddy(self):
        if self.misting_task:
            self.misting_task.cancel()
            try:
                await self.misting_task
            except asyncio.CancelledError:
                pass
            finally:
                self.misting_task = None

        if self.power_instance:
            self.power_instance = None

        logger.info("MistBuddy stopped successfully.")

_mistbuddy_manager = None
def get_mistbuddy_manager() -> MistBuddyManager:
    global _mistbuddy_manager
    if not _mistbuddy_manager:
        _mistbuddy_manager =  MistBuddyManager()
    return _mistbuddy_manager
