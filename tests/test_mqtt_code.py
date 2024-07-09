import pytest
from mqtt_code import MQTTClient

@pytest.fixture
def mqtt_client():
    client = MQTTClient(host='gus.local')
    return client

@pytest.fixture
def not_mqtt_client():
    client = MQTTClient(host='bad address')
    return client

def test_on_connect_success(mqtt_client):
    client = None
    userdata = None
    flags = None
    rc = 0  # Success code

    result = mqtt_client.on_connect(client, userdata, flags, rc)

    assert result == rc

def test_on_connect_failure(not_mqtt_client):
    client = None
    userdata = None
    flags = None
    rc = 1  # Failure code

    result = not_mqtt_client.on_connect(client, userdata, flags, rc)

    assert result == rc
