import json
import os
from dotenv import load_dotenv
load_dotenv()


from pydantic import BaseModel, Field
from typing import Dict, List

shared_path = os.getenv("shared_path", "GrowBuddies_shared")

class GlobalSettings(BaseModel):
    hostname: str
    host_ip: str
    incoming_port: int = Field(..., gt=0, lt=65536)
    log_level: str


class PIDConfig(BaseModel):
    active: bool
    setpoint: float
    Kp: float
    Ki: float
    Kd: float
    output_limits: List[int] = Field(..., min_items=2, max_items=2)
    integral_limits: List[int] = Field(..., min_items=2, max_items=2)
    tune_increment: float
    comparison_function: str
    mqtt_power_topics: List[str]
    telegraf_fieldname: str

class TentConfig(BaseModel):
    MistBuddy: PIDConfig
    CO2Buddy: PIDConfig

class Settings(BaseModel):
    global_settings: GlobalSettings
    pid_configs: Dict[str, TentConfig]

    @staticmethod
    def load() -> None:
        """Load the growbuddies_settings.json file and returns an instance of the Settings class.

        Raises:
            Exception: Returns a string letting the caller know the json file could not be opened.
        """
        try:
            filepath = os.path.join(shared_path, "growbuddies_settings.json")
            with open(filepath) as json_file:
                settings_dict = json.load(json_file)
        except FileNotFoundError as e:
            raise e
        settings = Settings(**settings_dict)
        return settings
