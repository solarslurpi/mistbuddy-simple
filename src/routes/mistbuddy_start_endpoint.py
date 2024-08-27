
import logging
from fastapi import APIRouter, Body, Depends
from pydantic import BaseModel, confloat, field_validator

import src.logging_config
from src.config import is_valid_tent_name
from src.service.mistbuddy_manager import MistBuddyManager, get_mistbuddy_manager

logger = logging.getLogger(__name__)

router = APIRouter()

class MistbuddyLiteForm(BaseModel):
    tent_name: str
    duration_on: confloat(gt=0, le=60)  # type: ignore

    @field_validator("tent_name")
    def validate_tent_name(cls, value):
        if not is_valid_tent_name(value):
            raise ValueError(f"Invalid tent name: {value}. Please check the growbuddies_settings file.")
        return value

@router.post("/mistbuddy-lite/start")
async def mistbuddy_lite_start(
    form_data: MistbuddyLiteForm = Body(...),
    mistbuddy_manager: MistBuddyManager = Depends(get_mistbuddy_manager)
):
    logger.info(f"Starting mistbuddy lite for tent {form_data.tent_name} with duration {form_data.duration_on}")
    await mistbuddy_manager.start_mistbuddy(form_data.tent_name, form_data.duration_on)
    return {"status": f"mistbuddy lite spewing mist every {form_data.duration_on} seconds each minute."}