import asyncio
import logging

import src.logging_config
from src.config import settings, get_power_settings
from src.service.mqtt_publish_code import MQTTClient

logger = logging.getLogger(__name__)

class PowerBuddy:
    def __init__(self, tent_name:str, host_ip: str):
        try:
            self.power_topics = get_power_settings(tent_name,"MistBuddy")
            if not self.power_topics:
                logger.error(f"No power topics returned for tent_name: {tent_name}")
                raise ValueError(f"No power topics returned for tent_name: {tent_name}")
        except AttributeError as e:
            logger.error(f"Error attempting to get the host_ip and power_topics from settings.  Error: {e}")
            raise e
        try:
            self.mqtt_client = MQTTClient(host_ip)

        except Exception as e:
            logger.error(f"Error creating the MQTT client.  Error: {e}")
            raise e

    async def power_on(self, seconds_on: float) -> None:
        for power_command in self.power_topics:
            # Define pulsetime_command before the try block
            parts = power_command.split("/")
            parts[-1] = "PulseTime"
            pulsetime_command = "/".join(parts)

            try:
                # TURN POWER ON.
                self.mqtt_client.publish(power_command, 1, qos=1)
                logger.info(f"Sent message to power on for {seconds_on} seconds.")

                # We will use numbers between 112 and 64900 for the PulseTime (e.g.: 112 - 100 = 12 seconds)
                pulsetime_on = seconds_on + 100
                logger.debug(
                    f"PulseTime: {pulsetime_on} Number seconds on: {pulsetime_on - 100}"
                )
                # LET TASMOTA KNOW HOW LONG TO KEEP THE POWER ON.
                self.mqtt_client.publish(pulsetime_command, pulsetime_on, qos=1)
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
