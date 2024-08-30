# Fixtures placed here are available to all tests in the tests directory.

import pytest
import json

from mistbuddy_lite_code import MistBuddyLiteController
from mistbuddy_lite_state_code import MistBuddyLiteState


@pytest.fixture(scope='session')
def name():
    return 'tent_one'

@pytest.fixture(scope='session')
def address():
    return '192.168.68.113'

@pytest.fixture(scope='session')
def duration_on():
    return 10

@pytest.fixture(scope='session')
def power_messages():
    return ["cmnd/mistbuddy_fan/POWER", "cmnd/mistbuddy_mister/POWER"]

@pytest.fixture
def mistbuddy_controller():
    controller = MistBuddyLiteController.get_mistbuddy_controller()
    return controller

@pytest.fixture
def mistbuddy_state(address,duration_on, name, power_messages):
    return MistBuddyLiteState(name=name, address=address, duration_on=duration_on, power_messages=power_messages)

@pytest.fixture()
def growbuddies_settings(tmp_path):
    """
    Leverages pytest's tmp_path fixture to simulate the presence of a 'growbuddies_settings.json' file.
    It creates a temporary file in a temporary directory, mimicking the actual settings file structure.
    Returns the path to this temporary file as a string.
    """

    settings_file = tmp_path / "growbuddies_settings.json"

    # Step 3: Write the JSON content to the temporary file
    content = {
        "global_settings": {
            "version": "0.1",
            "address": "192.168.68.113",
            "log_level": "DEBUG",
            "db_name": "gus",
            "incoming_port": 8095
        },
        "mqtt_power_messages": {
                "tent_one": {"mistbuddy":["cmnd/mistbuddy_fan/POWER", "cmnd/mistbuddy_mister/POWER"],"co2buddy":["cmnd/tent_one_co2buddy/POWER"]}
        },

    }
    with open(settings_file, "w") as f:
        json.dump(content, f)

    # Step 4: Yield the file path
    yield str(settings_file)

    # Cleanup is handled by pytest's tmp_path fixture