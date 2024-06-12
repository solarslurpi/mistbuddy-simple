import logging
from dotenv import load_dotenv
load_dotenv()

from mqtt_code import MQTTClient
from GrowBuddies_shared.logger_code import LoggerBase
from settings_model import Settings
import json

logger = LoggerBase.setup_logger("MistBuddyPower", logging.DEBUG)

mqtt_client = MQTTClient()
mqtt_client.start()

class PowerBuddy:
    def __init__(self):
        self.mqtt_client = MQTTClient()

    def get_power_topics_for_tent(self, tent_name: str, settings: Settings):
        try:
            power_topics = settings.pid_configs[tent_name].MistBuddy.mqtt_power_topics
            logger.debug(f"MistBuddy.get_power_topics_for_tent: Power topics: {json.dumps(power_topics, indent=4)}")
        except KeyError as e:
            raise f"Error finding the tent name in the settings file.  Error: {e}"
        return power_topics

    def turn_on_power(self, seconds_on: float, mqtt_topics) -> None:
        """
        Sends MQTT messages to turn on the power of the Tasmotized plugs used for MistBuddy and CO2Buddy for a specified duration.

        Args:
            seconds_on (float): The duration, in seconds, for which the power should be turned on.

        Raises:
            CommunicationError: If there is a failure in sending control commands.
            RuntimeError: If there is any other unexpected error.
        """
        # I was challenged because the power would be turned on but not off.  This got me to think there
        # was something wrong with threading.  But then I noticed the tasmotized devices were occassionally
        # not able to see Gus.  I had gotten a new wifi mesh and it doesn't seem to handle local ip names well.
        # gus.local was working until it is not.... so I had to hard code the ip address.  Yuk.

        # Set up a timer with the callback on completion.
        try:
            logger.debug(f"POWER ON FOR {seconds_on} SECONDS")
            self.publish_power_plug_messages(seconds_on, mqtt_topics)
        except Exception as e:
            logger.error(f"Unexpected error in turn_on_power: {e}")
            raise RuntimeError(f"Unexpected error: {e}")

    def publish_power_plug_messages( self, seconds_on: float, mqtt_topics) -> None:
        """
        Publish MQTT messages to control the power state. The method uses Tasmota's PulseTime command as a timer amount for how long to keep the power plug on.  For a quick timer, set the PulseTime between 1 and 111.  Each number represents 0.1 seconds.  If the PulseTime is set to 10, the power plug stays on for 1 second.  Longer times use setting values between 112 to 649000.  PulseTime 113 means 13 seconds: 113 - 100. PulseTime 460 = 460-100 = 360 seconds = 6 minutes.

        Args:
            power_state (int): Desired power state, either 1 (for on) or 0.
        """
        for power_command in mqtt_topics:
            mqtt_client.publish(power_command, 1, qos=1)
            # Split the topic by the '/'
            parts = power_command.split("/")
            # Replace the last part with 'PulseTime'
            parts[-1] = "PulseTime"
            # Join the parts back together to form the new topic
            pulsetime_command = "/".join(parts)
            # We will use numbers between 112 and 64900 for the PulseTime (e.g.: 112 - 100 = 12 seconds)
            pulsetime_on = seconds_on + 100
            logger.debug(
                f"PulseTime: {pulsetime_on} Number seconds on: {pulsetime_on - 100}"
            )
            mqtt_client.publish(pulsetime_command, pulsetime_on, qos=1)
            logger.debug(
                f"Topic {power_command} was turned on for {seconds_on} seconds."
            )

    def start(self):
        logger.debug("mistbuddy_power_code.start: Starting the MQTT client.")
        self.mqtt_client.start()

    def stop(self):
        logger.debug("mistbuddy_power_code.stop: Stopping the MQTT client.")
        self.cleanup()

    def cleanup(self):
        self.mqtt_client.stop()
        logger.debug("mistbuddy_power_code.cleanup: Stopped the MQTT client.")