import pytest
from unittest.mock import patch

from src.config import config
from src.service.power_code import PowerBuddy

@pytest.fixture
def host_ip():
    return config.get_host_ip()

@pytest.fixture(scope="session", autouse=True)
def load_config():
    config.load_settings('config.yaml')

@pytest.fixture
def mock_get_power_settings():
    with patch('src.service.power_code.get_power_settings') as mock:
        yield mock

@pytest.fixture
def mock_mqtt_client():
    with patch('src.service.power_code.MQTTClient') as mock:
        yield mock

@pytest.mark.parametrize("tent_name, should_succeed", [
    ("tent_one",True),
    ("tent_two", False),
    ("tent_three", False),
])
def test_power_buddy_init(tent_name, host_ip, should_succeed):
    if should_succeed:
        power_buddy = PowerBuddy(tent_name, host_ip)
        assert isinstance(power_buddy, PowerBuddy)

    else:
        with pytest.raises(ValueError):
            PowerBuddy(tent_name, host_ip)
