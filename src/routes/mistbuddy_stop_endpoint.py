import asyncio
import logging
from fastapi import APIRouter, Depends

from src.service.mistbuddy_manager import MistBuddyManager, get_mistbuddy_manager

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/api/v1/mistbuddy-lite/stop")
async def mistbuddy_lite_stop(manager: MistBuddyManager = Depends(get_mistbuddy_manager)):
    await manager.stop_mistbuddy()
    return {"status": "stopped misting."}