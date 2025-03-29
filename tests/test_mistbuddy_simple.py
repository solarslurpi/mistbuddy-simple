import asyncio
import pytest
import paho.mqtt.client as mqtt
import time
from queue import Queue, Empty # Use standard queue for thread safety
import threading

# Assuming your SimpleMistBuddy class is in src.mistbuddy_simple
from src.mistbuddy_simple import SimpleMistBuddy
from src.appconfig import AppConfig # Needed for config structure if used

# --- Configuration ---
TEST_BROKER_HOST = "localhost" # Your test broker host
TEST_BROKER_PORT = 1883
TEST_CONTROL_TOPIC = "cmnd/test-integ/mistbuddy/ONOFF"
TEST_POWER_TOPICS = ["cmnd/test-integ/mister/POWER", "cmnd/test-integ/fan/POWER"]
TEST_PULSETIME_TOPICS = ["cmnd/test-integ/mister/PulseTime", "cmnd/test-integ/fan/PulseTime"]

# --- Helper Fixture for Test MQTT Client ---

@pytest.fixture(scope="function") # New client for each test function
def test_mqtt_client_manager():
    """Provides a connected MQTT client for tests and handles cleanup."""
    received_messages = Queue() # Thread-safe queue

    def on_connect(client, userdata, flags, rc, properties=None):
        if rc == 0:
            print("Test Client Connected")
            # Subscribe to topics we want to monitor (power topics)
            for topic in TEST_POWER_TOPICS + TEST_PULSETIME_TOPICS:
                 client.subscribe(topic, qos=1)
                 print(f"Test Client Subscribed to: {topic}")
        else:
            print(f"Test Client Connection Failed: {rc}")
            pytest.fail(f"Test client failed to connect to MQTT broker: {rc}")

    def on_message(client, userdata, msg):
        print(f"Test Client Received: {msg.topic} -> {msg.payload.decode()}")
        received_messages.put((msg.topic, msg.payload.decode()))

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"test-integ-{time.time()}")
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        client.connect(TEST_BROKER_HOST, TEST_BROKER_PORT, 60)
        client.loop_start() # Start background thread
        # Wait briefly for connection and subscriptions
        time.sleep(0.5) 
        if not client.is_connected():
             pytest.fail("Test client could not connect within timeout.")
             
        # Yield the client and the queue
        yield client, received_messages
        
    finally:
        print("Test Client Cleaning up...")
        client.loop_stop()
        client.disconnect()
        print("Test Client Disconnected.")


# --- Test Cases ---

@pytest.mark.asyncio
async def test_integration_start_stop_cycle(test_mqtt_client_manager):
    """Test sending start and stop messages via MQTT."""
    test_client, received_queue = test_mqtt_client_manager
    
    # 1. Create and run the SimpleMistBuddy instance
    mistbuddy = SimpleMistBuddy(
        broker_ip=TEST_BROKER_HOST,
        control_topic=TEST_CONTROL_TOPIC,
        power_topics=TEST_POWER_TOPICS
    )
    # Run the mistbuddy in a background task
    mistbuddy_task = asyncio.create_task(mistbuddy.run())
    await asyncio.sleep(1.0) # Allow time for connection and subscription

    # --- Test Start ---
    print("Sending START command (10s)...")
    duration = 10
    expected_pulsetime = duration + 100
    test_client.publish(TEST_CONTROL_TOPIC, str(duration), qos=1)
    
    # 2. Verify power_on messages (PulseTime and POWER ON)
    expected_start_messages = {
        TEST_PULSETIME_TOPICS[0]: str(expected_pulsetime),
        TEST_POWER_TOPICS[0]: "ON",
        TEST_PULSETIME_TOPICS[1]: str(expected_pulsetime),
        TEST_POWER_TOPICS[1]: "ON",
    }
    received_start_messages = {}
    
    try:
        # Wait for the expected number of messages with a timeout
        for _ in range(len(expected_start_messages)):
             topic, payload = received_queue.get(timeout=5.0) 
             received_start_messages[topic] = payload
    except Empty:
        pytest.fail(f"Timeout waiting for START power messages. Received: {received_start_messages}")
        
    assert received_start_messages == expected_start_messages
    print("START power messages verified.")
    
    # 3. Let it run for a bit (less than a full cycle maybe)
    await asyncio.sleep(duration + 2) # Wait longer than duration

    # --- Test Stop ---
    print("Sending STOP command (0s)...")
    test_client.publish(TEST_CONTROL_TOPIC, "0", qos=1)

    # 4. Verify power_off messages (PulseTime 0 and POWER OFF)
    expected_stop_messages = {
        TEST_PULSETIME_TOPICS[0]: "0",
        TEST_POWER_TOPICS[0]: "OFF",
        TEST_PULSETIME_TOPICS[1]: "0",
        TEST_POWER_TOPICS[1]: "OFF",
    }
    received_stop_messages = {}
    try:
        for _ in range(len(expected_stop_messages)):
             topic, payload = received_queue.get(timeout=5.0)
             received_stop_messages[topic] = payload
    except Empty:
        pytest.fail(f"Timeout waiting for STOP power messages. Received: {received_stop_messages}")
        
    assert received_stop_messages == expected_stop_messages
    print("STOP power messages verified.")

    # 5. Cleanup: Cancel the mistbuddy task and wait for it
    print("Cleaning up mistbuddy task...")
    mistbuddy_task.cancel()
    try:
        await mistbuddy_task
    except asyncio.CancelledError:
        print("Mistbuddy task cancelled successfully.")
    print("Test finished.")

# Add more tests for:
# - Invalid duration messages
# - Repeated start messages
# - Broker disconnection/reconnection (more advanced)
