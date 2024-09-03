import asyncio
import logging

import src.logging_config

from src.config import config
from src.service.mqtt_publish_code import MQTTClient

logger = logging.getLogger(__name__)

class PowerBuddy:
    def __init__(self, tent_name:str, host_ip: str):
        try:
            self.power_topics = []
            self.mqtt = None
            self.power_topics = config.get_power_topics(tent_name,"MistBuddy")
            if not self.power_topics or len(self.power_topics) == 0:
                logger.error(f"No power topics returned for tent_name: {tent_name}")
                raise ValueError(f"No power topics returned for tent_name: {tent_name}")
            try:
                self.mqtt = MQTTClient(host=host_ip)
                logger.debug(f"MQTT client created for host: {host_ip}")
            except Exception as e:
                logger.error(f"Error setting up MQTT client", exc_info=True)
                raise
        except AttributeError as e:
            logger.error(f"Error attempting to get the host_ip and power_topics from settings.  Error: {e}")
            raise e

    async def power_on(self, seconds_on: float) -> None:
        for power_command in self.power_topics:
            # Define pulsetime_command before the try block
            parts = power_command.split("/")
            parts[-1] = "PulseTime"
            pulsetime_command = "/".join(parts)

            try:
                # TURN POWER ON.
                self.mqtt.publish(power_command, 1, qos=1)
                logger.info(f"Sent {power_command} to power on for {seconds_on} seconds.")

                # We will use numbers between 112 and 64900 for the PulseTime (e.g.: 112 - 100 = 12 seconds)
                pulsetime_on = seconds_on + 100
                logger.debug(
                    f"PulseTime: {pulsetime_on} Number seconds on: {pulsetime_on - 100}"
                )
                # LET TASMOTA KNOW HOW LONG TO KEEP THE POWER ON.
                self.mqtt.publish(pulsetime_command, pulsetime_on, qos=1)
            except Exception as e:
                error_message = (
                    f"Failed to publish MQTT message for command '{power_command}' "
                    f"or '{pulsetime_command}'. Duration: {seconds_on} seconds. Error: {e}"
                )
                logger.error(error_message)
                raise RuntimeError(error_message)


    async def async_timer(self,interval, stop_event,  seconds_on ):
        while not stop_event.is_set():
            await self.power_on( seconds_on )
            await asyncio.sleep(interval)
