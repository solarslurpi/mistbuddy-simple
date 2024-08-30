import logging
import pytest
import time
from logger_code import LoggerBase
from mqtt_code import MQTTClient

from logger_code import LoggerBase

logger = LoggerBase.setup_logger(__name__, logging.DEBUG)

@pytest.fixture
def mqtt_client(address):
    client = MQTTClient(host=address)
    return client

@pytest.fixture
def not_mqtt_client():
    client = MQTTClient(host='bad address')
    return client

def test_mqtt_publish(mqtt_client,power_messages):
    mqtt_client.start()
    for power_message in power_messages:
        logger.debug(power_message)
        # Turn the power switch off.
        mqtt_client.publish(power_message,1)
        # Set the pulse time.

    # assert mqtt_client.client.publish.call_count == 4
