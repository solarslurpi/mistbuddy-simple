import logging
from fastapi import  APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel, confloat, field_validator
from src.service.mistbuddy_manager import MistBuddyManager, get_mistbuddy_manager
from src.service.dependencies import get_mistbuddy_manager
from src.config import config

logger = logging.getLogger(__name__)

router = APIRouter()


class MistbuddyLiteForm(BaseModel):
    tent_name: str
    duration_on: confloat(gt=0, le=60)  # type: ignore

    @field_validator("tent_name")
    def check_tent_name(cls, v):
        if config.is_valid_tent_name(v) == False:
            raise ValueError(f"Invalid tent name: {v}")
        return v

@router.post("/start")
async def mistbuddy_lite_start(
    form_data: MistbuddyLiteForm = Body(...),
    mistbuddy_manager: MistBuddyManager = Depends(get_mistbuddy_manager),
):
    try:
        logger.debug(f"Starting mistbuddy lite in {form_data.tent_name} for {form_data.duration_on} seconds.")

        await mistbuddy_manager.start_mistbuddy(config.get_host_ip(), form_data.tent_name, form_data.duration_on)
        return {"status": f"mistbuddy lite spewing mist every {form_data.duration_on} seconds each minute."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stop")
async def mistbuddy_lite_stop(
    mistbuddy_manager: MistBuddyManager = Depends(get_mistbuddy_manager)
):
    try:
        await mistbuddy_manager.stop_mistbuddy()
        return {"status": "mistbuddy lite stopped"}
    except Exception as e:
        logger.error(f"Error stopping MistBuddy: {e}")
        raise HTTPException(status_code=500, detail=str(e))
