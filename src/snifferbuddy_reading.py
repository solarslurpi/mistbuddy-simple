
import asyncio
import logging
import re
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

from pydantic import BaseModel, Field

from ..GrowBuddies_shared.logger_code import LoggerBase

logger = LoggerBase.setup_logger("SnifferBuddyReading", logging.DEBUG)

class SnifferBuddyReading(BaseModel):
    name:Optional[str] = Field(default=None, description="unique name provided by the user to identify the SnifferBuddies within a grow tent.")
    version: str = Field(default="0.0.1", description="Version of the SnifferBuddy reading.")
    co2:float = Field(default=0,description="CO2 reading.")
    humidity:float = Field(default=0,description="humidity reading.")
    temperature:float = Field(default=0,description="temperature reading.")
    vpd: float = Field(default=0.0,description="vpd reading.")
    light: bool = Field(default=False, description="True if the light is on.")
    incoming_socket: Optional[asyncio.StreamReader] = None

    def __init__(self, host: str, port: int):
        self.host = host{
    "global_settings": {
        "hostname": "gus.local",
        "log_level": "DEBUG",
        "db_name": "gus",
        "pid_port": 8095,
        "tune_port": 8096
    },
    "pid_configs": {
        "tent_one": {
            "MistBuddy": {
                "active": true,
                "setpoint": 1.0,
                "Kp": 100.0,
                "Ki": 0.8,
                "Kd": 5,
                "output_limits": [0, 50],
                "integral_limits": [0, 30],
                "tune_start": 0,
                "tune_increment": 0,
                "comparison_function": "less_than",
                "mqtt_power_topics": ["cmnd/mistbuddy_fan/POWER", "cmnd/mistbuddy_mister/POWER"],
                "telegraf_fieldname": "vpd_mean",
                "num_bias_seconds_on": 20
            },
            "CO2Buddy": {
                "active": true,
                "setpoint": 1000,
                "Kp": 0.1,
                "Ki": 0.01,
                "Kd": 0.01,
                "output_limits": [0, 15],
                "integral_limits": [0, 12],
                "tune_start": 0,
                "tune_increment": 0,
                "comparison_function": "greater_than",
                "mqtt_power_topics": ["cmnd/stomabuddy/POWER"],
                "telegraf_fieldname": "CO2_mean",
                "num_bias_seconds_on": 0
            }
        }

    }
}

        self.port = port
        # Regular expression used to get the value from the telegraf line protocol.
        self.value_regex = re.compile(rf'{self.config["telegraf_fieldname"]}=([\d.]+)')

    async def setup_connection(self):
        self.incoming_socket, _ = await asyncio.open_connection(self.host, self.port)

    async def get_reading_generator(self):
        while True:
            try:
                packet = await self.incoming_socket.read(1024)
                decoded_str = packet.decode()
                logger.debug(f"snifferbuddy_reading.get_reading_generator: Incoming packet: {decoded_str}")

                value_match = self.value_regex.search(decoded_str)
                if value_match:
                    value = float(value_match.group(1))
                    yield value
                else:
                    logger.warning(
                        "snifferbuddy_reading.get_reading_generator: Value format mismatch in packet received from Telegraf"
                    )
            except asyncio.TimeoutError:
                logger.error("snifferbuddy_reading.get_reading_generator: Socket timeout.")
            except OSError as e:
                logger.error(f"snifferbuddy_reading.get_reading_generator: OS error {e}")
            except Exception as e:
                logger.error(f"snifferbuddy_reading.get_reading_generator:Unexpected error  {e}")
