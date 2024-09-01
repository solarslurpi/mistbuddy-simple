import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException

from src.config import config
from src.service.mistbuddy_manager import MistBuddyManager



@pytest.fixture
def host_ip():
    return config.get_host_ip()

@pytest.fixture
def mistbuddy_manager():
    return MistBuddyManager()

@pytest.fixture(scope="session", autouse=True)
def load_config():
    config.load_settings('config.yaml')

@pytest.mark.asyncio
async def test_start_mistbuddy_success(host_ip, mistbuddy_manager):
    with patch('src.service.mistbuddy_manager.PowerBuddy') as mock_power_buddy:
        mock_power_buddy.return_value.async_timer = AsyncMock()
        await mistbuddy_manager.start_mistbuddy(host_ip, "tent_one", 30)
        assert mistbuddy_manager.stop_event is not None
        assert mistbuddy_manager.timer_task is not None
        assert mistbuddy_manager.power_instance is not None
        mock_power_buddy.assert_called_once()
        mock_power_buddy.return_value.async_timer.assert_called_once_with(60, mistbuddy_manager.stop_event, 30)

@pytest.mark.asyncio
async def test_start_mistbuddy_value_error(host_ip, mistbuddy_manager):
    with patch('src.service.mistbuddy_manager.PowerBuddy', side_effect=ValueError):
        with pytest.raises(HTTPException) as exc_info:
            await mistbuddy_manager.start_mistbuddy(host_ip, "invalid_tent", 30)
        assert exc_info.value.status_code == 400
        assert "Invalid input parameters" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_start_mistbuddy_unexpected_error(host_ip, mistbuddy_manager):
    with patch('src.service.mistbuddy_manager.PowerBuddy', side_effect=Exception):
        with pytest.raises(HTTPException) as exc_info:
            await mistbuddy_manager.start_mistbuddy(host_ip, "tent_one", 30)
        assert exc_info.value.status_code == 500
        assert "Error starting MistBuddy" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_stop_mistbuddy(mistbuddy_manager, mocker):
    # Can't use async_mock to test cancelling the task because it doesn't support __await__.
    loop = asyncio.get_running_loop()
    async def dummy_task():
        await asyncio.sleep(1)
    task = loop.create_task(dummy_task())
    mistbuddy_manager.timer_task = task
    # Keep a reference to the mock object even after mistbuddy_manager is set to None. This way, we can check if the instance was called.
    power_instance_mock = mocker.AsyncMock()
    mistbuddy_manager.power_instance = power_instance_mock
    stop_event_mock = mocker.AsyncMock()
    mistbuddy_manager.stop_event = stop_event_mock

    # Execute
    await mistbuddy_manager.stop_mistbuddy()

    # Assert
    assert mistbuddy_manager.timer_task is None
    assert mistbuddy_manager.stop_event is None
    assert mistbuddy_manager.power_instance is None
    power_instance_mock.stop.assert_awaited_once()
    stop_event_mock.set.assert_called_once()

@pytest.mark.asyncio
async def test_stop_mistbuddy_no_active_instance(mistbuddy_manager):
    # Setup: Ensure all attributes are None
    mistbuddy_manager.timer_task = None
    mistbuddy_manager.power_instance = None
    mistbuddy_manager.stop_event = None

    # Execute
    await mistbuddy_manager.stop_mistbuddy()

    # Assert: No exceptions should be raised
    assert mistbuddy_manager.timer_task is None
    assert mistbuddy_manager.stop_event is None
    assert mistbuddy_manager.power_instance is None
