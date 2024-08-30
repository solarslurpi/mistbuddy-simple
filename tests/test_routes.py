import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException

from mistbuddy_lite import app
from src.service.mistbuddy_manager import MistBuddyManager

client = TestClient(app)

@pytest.fixture
def mock_mistbuddy_manager(mocker):
    mock_manager = mocker.AsyncMock(spec=MistBuddyManager)
    mocker.patch.object(MistBuddyManager, '__new__', return_value=mock_manager)
    return mock_manager

@pytest.mark.asyncio
async def test_mistbuddy_lite_start(mock_mistbuddy_manager):
    response = client.post(
        "/api/v1/start",
        json={"tent_name": "tent_one", "duration_on": 30}
    )

    print(f"Response status code: {response.status_code}")
    print(f"Response content: {response.content}")

    assert response.status_code == 200
    assert "mistbuddy lite spewing mist every 30.0 seconds each minute" in response.json()["status"]
    mock_mistbuddy_manager.start_mistbuddy.assert_awaited_once_with("tent_one", 30)

@pytest.mark.asyncio
async def test_mistbuddy_lite_start_invalid_tent_name():
    response = client.post(
        "/api/v1/start",
        json={"tent_name": "invalid_tent", "duration_on": 30}
    )

    assert response.status_code == 422
    assert "Invalid tent name" in response.json()["detail"][0]["msg"]

@pytest.mark.asyncio
async def test_mistbuddy_lite_start_invalid_duration():
    response = client.post(
        "/api/v1/start",
        json={"tent_name": "tent_one", "duration_on": 0}
    )

    assert response.status_code == 422
    assert "Input should be greater than 0" in response.json()["detail"][0]["msg"]

@pytest.mark.asyncio
async def test_mistbuddy_lite_stop(mock_mistbuddy_manager):
    response = client.get("/api/v1/stop")

    assert response.status_code == 200
    assert response.json() == {"status": "stopped misting."}
    mock_mistbuddy_manager.stop_mistbuddy.assert_called_once()

@pytest.mark.asyncio
async def test_mistbuddy_lite_start_exception(mock_mistbuddy_manager):
    mock_mistbuddy_manager.start_mistbuddy.side_effect = HTTPException(status_code=500, detail="Error starting MistBuddy")
    response = client.post(
        "/api/v1/start",
        json={"tent_name": "tent_one", "duration_on": 30}
    )

    assert response.status_code == 500
    assert "Error starting MistBuddy" in response.json()["detail"]

@pytest.mark.asyncio
async def test_mistbuddy_lite_stop_exception(mock_mistbuddy_manager):
    mock_mistbuddy_manager.stop_mistbuddy.side_effect = HTTPException(status_code=500, detail="Error stopping MistBuddy")
    response = client.get("/api/v1/stop")

    assert response.status_code == 500
    assert "Error stopping MistBuddy" in response.json()["detail"]
