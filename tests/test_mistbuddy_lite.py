# write the most important pytest for mistbuddy_lite_code.py
import asyncio
import pytest
from fastapi.testclient import TestClient
from mistbuddy_lite_code import MistBuddyLiteController, app
from mistbuddy_lite_state_code import MistBuddyLite_state

@pytest.fixture
def duration_on():
    return 10

@pytest.fixture
def mistbuddy_controller():
    controller = MistBuddyLiteController.get_mistbuddy_controller()
    return controller

@pytest.fixture
def mistbuddy_state(duration_on):
    return MistBuddyLite_state(name="tent_one", address="192.168.68.113", duration_on=duration_on, power_messages=["cmnd/tent_one_mistbuddy_fan/POWER", "cmnd/tent_one_mistbuddy_mister/POWER"])

@pytest.fixture
def client():
    return TestClient(app)

# ------------------------- initialization -------------------------
def test_mistbuddy_controller_initialization(mistbuddy_controller):
    """
    Test the initialization of MistBuddyLiteController.
    Goal: Ensure that the MistBuddyLiteController is properly initialized.
    """
    assert isinstance(mistbuddy_controller, MistBuddyLiteController)

def test_mistbuddy_controller_singleton():
    """
    Test the singleton behavior of MistBuddyLiteController.
    Goal: Ensure that the MistBuddyLiteController.get_mistbuddy_controller() method always returns the same instance.
    """
    controller1 = MistBuddyLiteController.get_mistbuddy_controller()
    controller2 = MistBuddyLiteController.get_mistbuddy_controller()
    assert controller1 is controller2

#------------------------- start_mistbuddy -------------------------
#  Ensure it correctly initializes PowerBuddy, stops any existing misting process, and starts the timer task as expected.


@pytest.mark.asyncio
async def test_start(mocker, mistbuddy_state):

    # Don't run the actual PowerBuddy code.  Mock it.
    mock_power_instance = mocker.Mock()
    mocker.patch('mistbuddy_lite_code.PowerBuddy', return_value=mock_power_instance)
    # The async_timer method is used to start the misting process.  Mock it. The test will determine if
    # the method is called, and called with the correct parameters. The test does not want to run the mister.
    mock_power_instance.async_timer = mocker.AsyncMock()


    # Create the controller instance
    controller = MistBuddyLiteController()
    # Now mock the stop method
    mocker.patch.object(controller, 'stop', new_callable=mocker.AsyncMock)
    # Run the start method
    await controller.start(mistbuddy_state)

    # Assertions
    controller.stop.assert_called_once()  # Ensure stop is called to stop any running misting
    mock_power_instance.start.assert_called_once()  # Ensure PowerBuddy start is called
    mock_power_instance.async_timer.assert_called_once_with(60, mocker.ANY, mistbuddy_state.duration_on)  # Ensure async_timer is called correctly

# ------------------------- stop_mistbuddy -------------------------
async def async_sleep():
    await asyncio.sleep(0)

@pytest.mark.asyncio
async def test_stop(mocker, mistbuddy_controller, mistbuddy_state):
    mock_power_instance = mocker.Mock()
    mocker.patch('power_code.PowerBuddy', return_value=mock_power_instance)
    # The async_timer method is used to start the misting process.  Mock it. The test will determine if
    # the method is called, and called with the correct parameters. The test does not want to run the
    # mister.
    mock_stop_event = mocker.Mock()
    # mock_timer_event = mocker.AsyncMock()
    # mock_timer_event.cancel = mocker.AsyncMock()
    mistbuddy_controller.power_instance = mock_power_instance
    mistbuddy_controller.stop_event = mock_stop_event
    # mistbuddy_controller.timer_task = mock_timer_event

    # Create the timer_task using the mocked async_timer
    # I could not get async

    await mistbuddy_controller.stop()

    # Assertions
    mock_power_instance.stop.assert_called_once()  # Ensure the power instance stop is called
    mock_stop_event.set.assert_called_once()  # Ensure the stop event is set
    # mock_timer_task.cancel.assert_called_once()  # Ensure the stop event is set
    # I give up on mocking cancel.  I tried.
    # Ensure the attributes are reset to None
    assert mistbuddy_controller.timer_task is None
    assert mistbuddy_controller.stop_event is None
    assert mistbuddy_controller.power_instance is None

def test_mistbuddy_lite_start_success(mocker, client, mistbuddy_state):
    payload = {
        "name": mistbuddy_state.name,
        "duration_on": mistbuddy_state.duration_on
    }
    mocker.patch('mistbuddy_lite_code.MistBuddyLiteController.start',new_callable = mocker.AsyncMock)
    response = client.post("/api/v1/mistbuddy-lite/start", json=payload)
    print(f"test_mistbuddy_lite_start_response.text: {response.text}")
    assert response.status_code == 200, response.text
    assert response.json() == {"status": f"mistbuddy lite spewing mist every {mistbuddy_state.duration_on} seconds each minute to the MistBuddy named {mistbuddy_state.name}."}

def test_mistbuddy_lite_start_failure(mocker, client):
    payload = {
        "name": "tent_one",
        "duration_on": 0 # Duration must be greater than 0 and less then 60
    }
    response = client.post("/api/v1/mistbuddy-lite/start", json=payload)
    assert response.status_code == 422
    assert response.text ==  '{"detail":[{"type":"greater_than","loc":["body","duration_on"],"msg":"Input should be greater than 0","input":0,"ctx":{"gt":0.0}}]}'

def test_mistbuddy_lite_stop_success(mocker, client):
    mocker.patch('mistbuddy_lite_code.MistBuddyLiteController.stop',new_callable = mocker.AsyncMock)
    response = client.get("/api/v1/mistbuddy-lite/stop")
    assert response.status_code == 200, response.text
    assert response.json() == {"status": "stopped misting."}

def test_mistbuddy_lite_stop_post_failure(mocker, client):
    mocker.patch('mistbuddy_lite_code.MistBuddyLiteController.stop',new_callable = mocker.AsyncMock)
    response = client.post("/api/v1/mistbuddy-lite/stop")
    assert response.status_code == 405
    assert response.json() == {"detail":"Method Not Allowed"}