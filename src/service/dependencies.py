from fastapi import Request
from src.service.mistbuddy_manager import MistBuddyManager
from src.config import AppSettings

def get_mistbuddy_manager(request: Request) -> MistBuddyManager:
    return request.app.state.mistbuddy_manager

def get_settings(request: Request) -> AppSettings:
    return request.app.state.settings
