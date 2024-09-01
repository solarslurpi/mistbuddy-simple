import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from mistbuddy_lite import create_app
from src.config import config
from src.routes.routes import MistbuddyLiteForm


# Mock MistBuddyManager to avoid actual hardware interactions during tests
class MockMistBuddyManager:
    async def start_mistbuddy(self, tent_name, duration_on):
        pass

    async def stop_mistbuddy(self):
        pass

@pytest.fixture
def test_app():
    app = create_app("config.yaml")
    app.state.mistbuddy_manager = MockMistBuddyManager()
    return app

@pytest.fixture
def client(test_app):
    return TestClient(test_app)

def test_mistbuddy_lite_start(client, test_app):
    response = client.post("/api/v1/start", json={"tent_name": "tent_one", "duration_on": 30})
    assert response.status_code == 200
    assert "status" in response.json()

def test_mistbuddy_lite_stop(client):
    response = client.get("/api/v1/stop")
    assert response.status_code == 200
    assert "status" in response.json()

def test_mistbuddy_lite_form_invalid_tent_name():
    config.load_settings("config.yaml")
    with pytest.raises(ValidationError) as exc_info:
        MistbuddyLiteForm(tent_name="invalid_tent", duration_on=30)

    assert "Invalid tent name: invalid_tent" in str(exc_info.value)

def test_mistbuddy_lite_start_exception(client, mocker):
    mock_manager = MockMistBuddyManager()
    mock_manager.start_mistbuddy = mocker.Mock(side_effect=Exception("Test exception"))
    client.app.state.mistbuddy_manager = mock_manager

    response = client.post("/api/v1/start", json={"tent_name": "tent_one", "duration_on": 30})
    assert response.status_code == 500
    assert response.json() == {"detail": "Test exception"}

def test_mistbuddy_lite_stop_exception(client, mocker):
    mock_manager = MockMistBuddyManager()
    mock_manager.stop_mistbuddy = mocker.Mock(side_effect=Exception("Test exception"))
    client.app.state.mistbuddy_manager = mock_manager

    response = client.get("/api/v1/stop")
    assert response.status_code == 500
    assert response.json() == {"detail": "Test exception"}
