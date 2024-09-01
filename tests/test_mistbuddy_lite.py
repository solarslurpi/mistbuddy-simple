import pytest

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mistbuddy_lite import create_app
from src.config import config
from src.service.mistbuddy_manager import MistBuddyManager

def test_create_app():
    # Create the app
    app = create_app("config.yaml")

    # Test that the app is an instance of FastAPI
    assert isinstance(app, FastAPI)

    # Test that CORS middleware has been added.
    cors_middleware = next((m for m in app.user_middleware if isinstance(m.cls, type(CORSMiddleware))), None)
    assert cors_middleware is not None, "CORS middleware not found"

    # Test that the router has been included.
    assert any(r.path.startswith("/api/v1") for r in app.routes), "API router not found"

    assert app.router.lifespan is not None, "Lifespan not set on app"


@pytest.mark.asyncio
async def test_lifespan_mistbuddy_manager_instance():
    app = create_app("config.yaml")

     # Check if mistbuddy manager is instantiated correctly.
    async with app.router.lifespan_context(app):
        assert hasattr(app.state, 'mistbuddy_manager'), "MistBuddyManager not created during startup"
        assert isinstance(app.state.mistbuddy_manager, MistBuddyManager), "app.state.mistbuddy_manager is not an instance of MistBuddyManager"