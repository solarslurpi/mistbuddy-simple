import asyncio
from paho.mqtt import client as mqtt
from typing import List, Optional
import math
import logging # Use standard logging

# Get a logger specific to this module
logger = logging.getLogger(__name__) # Use module name for logger

class SimpleMistBuddy:
    # __init__ now accepts specific config values + power topics
    def __init__(self, broker_ip: str, control_topic: str, power_topics: List[str]):
        """Initialize using specific configuration values."""
        logger.info(f"Initializing MistBuddy for control topic: {control_topic}")
        # Store the passed-in config values
        self.broker_ip = broker_ip # Use consistent naming
        self.control_topic = control_topic
        self.power_topics = power_topics # Store power topics

        if not self.power_topics:
             logger.warning(f"No power topics provided for {control_topic}. Power control will be simulated.")

        # Initialize other state
        self.misting_task: Optional[asyncio.Task] = None # Added type hint
        self.loop: Optional[asyncio.AbstractEventLoop] = None # Added type hint
        self.client: Optional[mqtt.Client] = None # Added type hint

        # Setup MQTT client (uses self.broker_ip now)
        self._setup_mqtt_client()

    def _setup_mqtt_client(self):
        """Setup MQTT client - still in regular Python context."""
        try:
            # Add a unique client ID suffix for each instance if running multiple
            # client_id = f"mistbuddy-{self.control_topic.replace('/', '_')}-{random.randint(1000,9999)}"
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2) # Consider adding client_id
            self.client.on_connect = self._on_connect
            self.client.on_message = self._on_message
            # Use the broker IP stored during __init__
            logger.info(f"Connecting to MQTT broker at {self.broker_ip}")
            self.client.connect(self.broker_ip)
        except Exception as e:
            logger.error(f"Failed to setup or connect MQTT client for {self.control_topic}: {e}", exc_info=True)
            raise ConnectionError("Failed to initialize MQTT connection") from e

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
        """MQTT connect callback - runs in MQTT thread."""
        if reason_code == 0:
            logger.info(f"Successfully connected to MQTT broker {self.broker_ip} for {self.control_topic}.")
            try:
                client.subscribe(self.control_topic)
                logger.info(f"Subscribed to control topic: {self.control_topic}")
            except Exception as e:
                 logger.error(f"Failed to subscribe to {self.control_topic}: {e}", exc_info=True)
        else:
            # Log specific reason codes if needed
            logger.error(f"Failed to connect MQTT for {self.control_topic}. Reason code: {reason_code}")

    def _on_message(self, client, userdata, msg):
        """MQTT message callback - runs in MQTT thread, must use run_coroutine_threadsafe."""
        if self.loop is None:
             logger.error(f"Event loop not available in _on_message ({self.control_topic}). Cannot schedule task.")
             return
        try:
            if msg.topic == self.control_topic:
                try:
                    payload_str = msg.payload.decode()
                    seconds = int(payload_str)
                    logger.debug(f"Received control message on {self.control_topic}: {seconds} seconds")
                    if seconds > 0:
                        # Bridge from MQTT thread to async context
                        # Analogy:
                        #  Setup: The MQTT Worker is in one thread, the Manager is in another thread.
                        #           The two work autonomously.
                        #  The MQTT Worker receives a physical work order (the MQTT message).
                        #  The work order requires action from start_misting.
                        #  The MQTT Worker can't do the Manager's specialized async work (start_misting).
                        #  So, the Worker takes the work order and puts it into a special, thread-safe inbox (run_coroutine_threadsafe) that automatically notifies the Manager (self.loop).
                        #  The Manager, when free, checks their notified inbox, picks up the work order, and performs the start_misting task using their async skills.
                        asyncio.run_coroutine_threadsafe(
                            self.start_misting(seconds),
                            self.loop
                        )
                        logger.info(f"Scheduled misting cycle start: {seconds}s for {self.control_topic}")
                    else:
                        # Schedule stop_misting for consistency
                        asyncio.run_coroutine_threadsafe(
                             self.stop_misting_async(), # Use an async version of stop
                             self.loop
                        )
                        logger.info(f"Scheduled misting cycle stop for {self.control_topic}")
                except ValueError:
                     logger.warning(f"Invalid duration value received on {self.control_topic}: '{payload_str}'")
                except Exception as e: # Catch errors during scheduling
                     logger.error(f"Error scheduling task from _on_message ({self.control_topic}): {e}", exc_info=True)
            # else:
            #     logger.debug(f"Ignoring message on unexpected topic: {msg.topic}")
        except Exception as e:
            logger.error(f"Error processing message in _on_message ({self.control_topic}): {e}", exc_info=True)

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
                logger.info(f"Misting ON for {duration}s ({self.control_topic})")
                self.power_on(duration)
                # Calculate sleep time accurately
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
