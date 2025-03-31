import asyncio
from paho.mqtt import client as mqtt
from typing import List, Optional, Any
import math
import logging # Use standard logging
import json # Ensure json is imported
# Import the specific config model needed
from src.appconfig import LightCheckSettings

# Get a logger specific to this module
logger = logging.getLogger(__name__) # Use module name for logger

class MistBuddySimple:
    # __init__ now accepts specific config values + power topics
    def __init__(self,
                 broker_ip: str,
                 control_topic: str,
                 power_topics: List[str],
                 light_check_settings: LightCheckSettings): # Use the explicit config settings object
        """
        Initialize the MistBuddy controller.
        """
        logger.info(f"Initializing MistBuddy:")
        logger.info(f"  Control Topic: {control_topic}")
        logger.info(f"  Broker IP: {broker_ip}")
        logger.info(f"  Power Topics: {power_topics}")
        logger.info(f"  Light Check Command Topic: {light_check_settings.light_on_query_topic}")
        logger.info(f"  Light Check Response Topic: {light_check_settings.light_on_response_topic}")

        # Store basic configuration
        self.broker_ip = broker_ip
        self.control_topic = control_topic
        self.power_topics = power_topics

        # --- Store Light Check Configuration ---
        self.light_query_cmd_topic = light_check_settings.light_on_query_topic
        self.light_query_resp_topic = light_check_settings.light_on_response_topic
        self.light_check_on_val = light_check_settings.light_on_value
        self.light_check_timeout = light_check_settings.response_timeout

        # Validate power topics
        if not self.power_topics:
             logger.warning(f"No power topics provided for {control_topic}. Power control will be simulated.")

        # Initialize state variables
        self.misting_task: Optional[asyncio.Task] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.client: Optional[mqtt.Client] = None
        # Initialize the Future placeholder
        self.light_check_future: Optional[asyncio.Future] = None

        # Setup the MQTT client instance
        self._setup_mqtt_client()

    def _setup_mqtt_client(self):
        """Setup MQTT client - still in regular Python context."""
        try:

            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2) # Consider adding client_id
            self.client.on_connect = self._on_connect
            self.client.on_message = self._on_message
            # Use the broker IP stored during __init__
            broker_ip_str = str(self.broker_ip)
            logger.info(f"Connecting to MQTT broker at {broker_ip_str}")
            self.client.connect(broker_ip_str)

        except Exception as e:
            logger.error(f"Failed to setup or connect MQTT client for {self.control_topic}: {e}", exc_info=True)
            raise ConnectionError(f"Failed to initialize MQTT connection for {self.control_topic}") from e

    def _publish(self, topic: str, payload: str | int | float, qos: int = 1):
        """Helper method to publish MQTT messages."""
        if not self.client or not self.client.is_connected():
            logger.error(f"MQTT client not connected ({self.control_topic}). Cannot publish to {topic}")
            return False # Indicate failure
        try:
            # Convert payload to string if it's not already
            if not isinstance(payload, str):
                payload_str = str(payload)
            else:
                 payload_str = payload

            logger.debug(f"Publishing to {topic} ({self.control_topic}): {payload_str}")
            result = self.client.publish(topic, payload_str, qos=qos)
            result.wait_for_publish(timeout=5.0) # Wait for publish confirmation (optional)
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                 logger.warning(f"Failed to publish to {topic} ({self.control_topic}). Return code: {result.rc}")
                 return False
            return True # Indicate success
        except ValueError as e: # Catches timeout from wait_for_publish
             logger.warning(f"Timeout waiting for publish confirmation to {topic} ({self.control_topic}): {e}")
             return False
        except Exception as e:
            logger.error(f"Error publishing to {topic} ({self.control_topic}): {e}", exc_info=True)
            return False


    def _on_connect(self, client, userdata, flags, reason_code, properties):
        """
        MQTT connect callback - subscribes to necessary topics upon connection.
        Runs in the MQTT client's thread.
        """
        # Check if the connection was successful (reason_code 0)
        if reason_code == 0:
            logger.info(f"Successfully connected to MQTT broker {self.broker_ip} for {self.control_topic}.")
            try:
                # Subscribe to the main control topic for this mistbuddy instance
                client.subscribe(self.control_topic)
                logger.info(f"Subscribed to control topic: {self.control_topic}")

                # Subscribe to the light check response topic
                client.subscribe(self.light_query_resp_topic)
                logger.info(f"Subscribed to light check response topic: {self.light_query_resp_topic}")
                # --- END SUBSCRIPTION ---

            except Exception as e:
                 # Log error if any subscription fails
                 logger.error(f"Failed to subscribe to required topics ({self.control_topic}, {self.light_query_resp_topic}) during on_connect for {self.control_topic}: {e}", exc_info=True)
                 # Optionally, consider how to handle failed subscriptions (e.g., prevent operation)
        else:
            # Log error if the initial connection failed
            logger.error(f"Failed to connect MQTT for {self.control_topic}. Reason code: {reason_code}")

    def _on_message(self, client, userdata, msg):
        """
        MQTT message callback - Decodes payload and dispatches to specific handlers based on topic.
        Runs in the MQTT client's thread.
        """
        # Ensure the asyncio loop is available (needed by handlers via run_coroutine_threadsafe)
        if self.loop is None:
             logger.error(f"Event loop not available in _on_message ({self.control_topic}). Cannot process message for topic '{msg.topic}'.")
             return

        # 1. Decode Payload (handle potential errors)
        try:
            payload_str = msg.payload.decode('utf-8')
            logger.debug(f"Received message on topic '{msg.topic}': {payload_str}")
        except UnicodeDecodeError:
            logger.warning(f"Could not decode payload on topic '{msg.topic}' as UTF-8.")
            return
        except Exception as e:
            logger.error(f"Unexpected error decoding payload on topic '{msg.topic}': {e}", exc_info=True)
            return

        # 2. Dispatch based on Topic
        try:
            if msg.topic == self.control_topic:
                self._handle_control_message(payload_str)
            elif msg.topic == self.light_query_resp_topic:
                self._handle_light_response(payload_str)
            # else: # Optional: Log unhandled topics
            #     logger.debug(f"Ignoring message on unhandled topic: {msg.topic}")
        except Exception as e:
            # Catch unexpected errors during handler execution
            logger.error(f"Error processing message for topic '{msg.topic}' in handler: {e}", exc_info=True)


    def _handle_control_message(self, payload_str: str):
        """Handles incoming messages on the misting control topic."""
        try:
            seconds = int(payload_str)
            logger.debug(f"Processing control message for {self.control_topic}: {seconds} seconds")
            if seconds > 0:
                # Schedule start_misting (which will check lights)
                asyncio.run_coroutine_threadsafe(self.start_misting(seconds), self.loop)
                logger.info(f"Scheduled misting START: duration={seconds}s for {self.control_topic}")
            else:
                # Schedule stop_misting
                asyncio.run_coroutine_threadsafe(self.stop_misting_async(), self.loop)
                logger.info(f"Scheduled misting STOP for {self.control_topic}")
        except ValueError:
             logger.warning(f"Invalid integer value received on control topic {self.control_topic}: '{payload_str}'")
        except Exception as e: # Catch errors during scheduling
             logger.error(f"Error scheduling task from control message ({self.control_topic}): {e}", exc_info=True)


    def _handle_light_response(self, payload_str: str):
        """Handles incoming messages on the light status response topic."""
        logger.debug(f"Processing potential light status response on {self.light_query_resp_topic}")
        # Check if we are actually waiting for this response via the Future
        active_future = self.light_check_future # Local reference for safety
        if active_future and not active_future.done():
            try:
                # Parse the JSON payload from the response
                data = json.loads(payload_str)
                # ASSUMPTION: Look for the hardcoded 'Mem1' key
                key_to_check = "Mem1"
                if key_to_check in data:
                    value = data[key_to_check]
                    logger.debug(f"Parsed light status response: {key_to_check} = {value}")
                    # Set the result on the waiting Future to unblock _check_light_status
                    active_future.set_result(value)
                else:
                     logger.warning(f"Response on {self.light_query_resp_topic} missing assumed key '{key_to_check}'. Payload: {payload_str}")
                     # Signal failure if key is missing
                     active_future.set_exception(KeyError(f"Assumed key '{key_to_check}' not found in response"))
            except json.JSONDecodeError:
                logger.warning(f"Could not decode JSON from response topic {self.light_query_resp_topic}: {payload_str}")
                # Signal failure if JSON is invalid
                active_future.set_exception(ValueError("Invalid JSON response for light status"))
            except Exception as e:
                 logger.error(f"Error processing light status response payload on {self.light_query_resp_topic}: {e}", exc_info=True)
                 # Signal failure for other processing errors
                 active_future.set_exception(e)
        else:
             # Log if we received a response but weren't actively waiting
             logger.debug(f"Received light status response on {self.light_query_resp_topic}, but not currently waiting for it.")
    async def _check_light_status(self) -> bool:
        """
        Asynchronously checks the light status via MQTT request/response.

        Sends a command to query Mem1 on the configured checker device and waits
        for a response handled by _on_message/_handle_light_response.

        Returns:
            bool: True if lights are considered ON based on the response,
                  False if lights are OFF, check times out, or an error occurs.
        """
        # Precheck
        # Am I already waiting for an answer about the light status? 
        if self.light_check_future and not self.light_check_future.done():            # 2. AND that previous check has NOT finished yet (its result/exception hasn't been set)
            logger.warning(f"Light status check already in progress for {self.control_topic}. Aborting new check.")
            return False 
        # 1. Setup the Future to wait for the response
        self.light_check_future = self.loop.create_future()
        logger.info(f"Requesting light status check via topic: {self.light_query_cmd_topic}")

        # 2. Publish the command to trigger the response
        published = self._publish(self.light_query_cmd_topic, "") # Payload usually ignored for Mem query

        if not published:
            logger.error(f"Failed to publish light status query command to {self.light_query_cmd_topic}.")
            if self.light_check_future and not self.light_check_future.done():
                self.light_check_future.cancel("Publish failed")
            self.light_check_future = None
            return False # Assume lights OFF if we can't even ask
              # 3. Wait for the response (or timeout)
        lights_on = False # Default to False (safe state)
        try:
            logger.debug(f"Waiting up to {self.light_check_timeout}s for light status response on {self.light_query_resp_topic}")
            result = await asyncio.wait_for(self.light_check_future, timeout=self.light_check_timeout)

            # 4. Process the result received via the Future
            logger.debug(f"Received light status check result: {result}")
            try:
                 # Compare the received result with the configured 'on' value
                 result_val = int(result)
                 config_on_val = int(self.light_check_on_val)
                 lights_on = (result_val == config_on_val)
                 logger.info(f"Light status check result for {self.control_topic}: Mem1={result_val} -> {'ON' if lights_on else 'OFF'}")
            except (ValueError, TypeError) as e:
                 logger.warning(f"Could not interpret light status result '{result}' as integer for comparison: {e}")
                 lights_on = False # Treat uninterpretable result as OFF

        except asyncio.TimeoutError:
            logger.warning(f"Timeout waiting for light status response on {self.light_query_resp_topic} for {self.control_topic}. Assuming lights OFF.")
            lights_on = False
        except asyncio.CancelledError:
             logger.info(f"Light status check cancelled for {self.control_topic}.")
             lights_on = False
        except Exception as e:
            logger.error(f"Error occurred during light status check for {self.control_topic}: {e}", exc_info=True)
            lights_on = False
        finally:
            # 5. Clean up the Future - crucial!
            self.light_check_future = None
            logger.debug("Light check future cleared.")

        # 6. Return the determined state
        return lights_on
    # --- END NEW ME
    # --- Power control implementation ---
    def power_on(self, duration: float):
        """Control the power ON using Tasmota PulseTime logic."""
        # Check if power control is configured (i.e., if power_topics list is not empty)
        if not self.power_topics:
            logger.info(f"(Simulated) Power ON for {duration} seconds on topic {self.control_topic}")
            return

        # PulseTime logic requires a positive duration
        if duration <= 0:
            logger.warning(f"Requested power_on duration ({duration}) is not positive for {self.control_topic}. Turning off instead.")
            self.power_off() # Call power_off if duration is invalid
            return

        # Tasmota PulseTime: 1..111 is off, 112..64900 is seconds + 100
        pulsetime_val = math.ceil(duration) + 100 # Use ceiling for safety
        if pulsetime_val < 112: pulsetime_val = 112 # Minimum effective PulseTime
        if pulsetime_val > 64900: pulsetime_val = 64900 # Maximum PulseTime

        # Calculate the actual duration Tasmota will use based on the final PulseTime value
        actual_seconds = pulsetime_val - 100
        logger.info(f"Turning Power ON via PulseTime ({pulsetime_val} -> {actual_seconds}s) for topics under {self.control_topic}")
        
        # Iterate through each configured power topic to send commands
        success_count = 0
        for topic in self.power_topics:
            # Check if it's a standard Tasmota POWER topic (ends with /POWER)
            if topic.endswith("/POWER"):
                # Derive the corresponding PulseTime topic by replacing POWER with PulseTime
                pulsetime_topic = topic[:-len("POWER")] + "PulseTime"
                
                # Step 1: Set the PulseTime timer on the Tasmota device FIRST.
                # This tells Tasmota how long to stay ON after the next POWER ON command.
                if self._publish(pulsetime_topic, pulsetime_val):
                     # Step 2: If PulseTime was set successfully, send the POWER ON command.
                     # Tasmota will turn the relay ON and automatically turn it OFF after 'actual_seconds'.
                    if self._publish(topic, "ON"): # Use "ON" string for Tasmota POWER command
                        success_count += 1
            else:
                # Log if the configured topic doesn't follow the expected pattern
                logger.warning(f"Cannot derive PulseTime topic from non-standard POWER topic: {topic} ({self.control_topic})")
            
        # Log if not all commands were published successfully (e.g., MQTT errors)
        if success_count < len(self.power_topics):
             logger.warning(f"Published power_on commands successfully for only {success_count}/{len(self.power_topics)} topics ({self.control_topic})")


    def power_off(self):
        """Control the power OFF."""
        if not self.power_topics:
            logger.info(f"(Simulated) Power OFF on topic {self.control_topic}")
            return

        logger.info(f"Turning Power OFF for topics under {self.control_topic}")
        
        # Iterate through each configured power topic
        success_count = 0
        for topic in self.power_topics:
            # Main Step: Send the POWER OFF command to turn the relay off immediately.
            if self._publish(topic, "OFF"): # Use "OFF" string for Tasmota POWER command
                 success_count += 1             
        # Log if not all commands were published successfully
        if success_count < len(self.power_topics):
             logger.warning(f"Published power_off commands successfully for only {success_count}/{len(self.power_topics)} topics ({self.control_topic})")

    # --- Misting task management ---
    async def stop_misting_async(self):
         """Async version of stopping the misting cycle."""
         logger.debug(f"stop_misting_async called for {self.control_topic}")
         task_to_clear = self.misting_task # Reference task before potential cancellation race
         if task_to_clear and not task_to_clear.done():
             logger.info(f"Cancelling active misting task for {self.control_topic}")
             task_to_clear.cancel()
             try:
                 await asyncio.wait_for(task_to_clear, timeout=2.0)
             except asyncio.CancelledError:
                 logger.debug(f"Misting task ({self.control_topic}) successfully cancelled.")
             except asyncio.TimeoutError:
                  logger.warning(f"Timeout waiting for misting task ({self.control_topic}) to cancel.")
             except Exception as e:
                 logger.error(f"Error awaiting task cancellation for {self.control_topic}: {e}", exc_info=True)
             finally:
                 # Clear only if it's the same task we started cancelling
                 if self.misting_task is task_to_clear:
                      self.misting_task = None
         else:
             logger.debug(f"No active misting task to stop for topic {self.control_topic}")

         # Ensure power is off after attempting to stop/clear the task
         self.power_off()


    async def start_misting(self, duration: float):
        """Start misting cycle - runs in async context."""
        logger.debug(f"start_misting called for topic {self.control_topic} with duration: {duration}")
        if duration <= 0:
            logger.warning(f"Requested misting duration ({duration}) is not positive for {self.control_topic}. Stopping any active cycle.")
            await self.stop_misting_async()
            return

        # Stop and await previous task before starting new one
        await self.stop_misting_async()

        logger.info(f"Starting new misting cycle task for {self.control_topic} ({duration}s duration)")
        self.misting_task = asyncio.create_task(self.misting_cycle(duration))


    async def misting_cycle(self, duration: float):
        """Run the misting cycle - runs in async context."""
        logger.debug(f"Entered misting_cycle for {self.control_topic} with duration: {duration}")
        # Basic validation already done in start_misting, but double check < 60
        if duration >= 60:
             logger.error(f"Misting duration ({duration}) must be less than 60 seconds. Stopping cycle for {self.control_topic}.")
             self.power_off() # Ensure power is off
             return

        try:
            while True:
                logger.info(f"Checking light status before starting misting for {self.control_topic}...")
                lights_are_on = await self._check_light_status()
                if lights_are_on:
                    # Lights are ON, proceed with turning power on
                    logger.info(f"Lights ON. Misting ON for {duration}s ({self.control_topic})")
                    self.power_on(duration)
                else:
                    # Lights are OFF, skip turning power on for this pulse
                    logger.info(f"Lights OFF. Skipping misting pulse for this cycle ({self.control_topic}).")
                # Calculate sleep time s
                sleep_duration = 60.0 - duration
                logger.debug(f"Misting cycle ({self.control_topic}) sleeping for {sleep_duration:.1f}s")
                await asyncio.sleep(sleep_duration)
        except asyncio.CancelledError:
            logger.info(f"Misting cycle cancelled externally for {self.control_topic}")
            # Power off is handled in stop_misting_async which is the only way this should be cancelled
            # self.power_off() # Redundant if stop_misting_async is always used
            # Do not re-raise CancelledError here, let the caller handle it
        except Exception as e:
            logger.error(f"Error within misting cycle for {self.control_topic}: {e}", exc_info=True)
            self.power_off() # Ensure power is off on other errors


    async def run(self):
        """Main application loop - Manages MQTT loop and task status."""
        self.loop = asyncio.get_running_loop()
        if not self.client:
             logger.critical(f"MQTT client not initialized for {self.control_topic}. Cannot run.")
             return

        try:
            self.client.loop_start()
        except Exception as e:
             logger.critical(f"Failed to start MQTT network loop for {self.control_topic}: {e}", exc_info=True)
             return

        logger.info(f"Started main loop for MistBuddy controlling {self.control_topic}")

        try:
            while True:
                if not self.client.is_connected():
                    logger.warning(f"MQTT client disconnected for {self.control_topic}. Attempting to reconnect is handled by paho-mqtt.")
                    # Paho-mqtt attempts reconnect automatically, we just wait.

                # Check task status periodically
                task_to_check = self.misting_task
                if task_to_check and task_to_check.done():
                    logger.info(f"Misting task for {self.control_topic} has finished.")
                    try:
                        task_to_check.result() # Check for exceptions
                    except asyncio.CancelledError:
                        logger.debug(f"Misting task ({self.control_topic}) finished due to cancellation.")
                    except Exception as e:
                        logger.error(f"Misting task ({self.control_topic}) failed unexpectedly: {e}", exc_info=True)
                    # Clear task only if it hasn't changed due to race condition
                    if self.misting_task is task_to_check:
                        self.misting_task = None

                # Heartbeat sleep
                await asyncio.sleep(5)

        except asyncio.CancelledError:
            logger.info(f"Main loop cancellation requested for {self.control_topic}. Shutting down.")
        finally:
            logger.info(f"Cleaning up resources for {self.control_topic}...")
            # Ensure misting stops and task is awaited
            await self.stop_misting_async()

            # Stop the MQTT network loop
            if self.client:
                try:
                    # No need to explicitly disconnect if loop_stop is called? Check docs.
                    # self.client.disconnect() # Might interfere with clean LWT?
                    self.client.loop_stop() # Stops the background thread
                    logger.info(f"MQTT network loop stopped for {self.control_topic}.")
                except Exception as e:
                     logger.error(f"Error during MQTT cleanup for {self.control_topic}: {e}", exc_info=True)

            logger.info(f"Shutdown complete for {self.control_topic}")
