import json
import os
from dotenv import load_dotenv
load_dotenv()


from pydantic import BaseModel, Field,  PrivateAttr
from typing import Dict, List

SHARED_PATH = os.getenv("SHARED_PATH", "GrowBuddies_shared")

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

class SettingsModel(BaseModel):
    global_settings: GlobalSettings
    pid_configs: Dict[str, TentConfig]

class Settings:
    _instance = None
    _settings_instance: SettingsModel = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Settings, cls).__new__(cls)
            cls._settings_instance = None  # Ensure this is reset for the new instance
        return cls._instance


    @classmethod
    def load(cls) -> SettingsModel:
        """Load the growbuddies_settings.json file and return an instance of the SettingsModel class.

        Raises:
            FileNotFoundError: If the JSON file could not be opened.
        """
        if cls._settings_instance is not None:
            return cls._settings_instance

        try:
            filepath = os.path.join(SHARED_PATH, "growbuddies_settings.json")
            with open(filepath) as json_file:
                settings_dict = json.load(json_file)
            cls._settings_instance = SettingsModel(**settings_dict)
            print(f"Loaded settings: {cls._settings_instance}")  # Debugging statement
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Could not open the settings file: {e}")
        except Exception as e:
            raise Exception(f"An error occurred while loading the settings: {e}")

        return cls._settings_instance

    @classmethod
    def is_valid_tent_name(cls, tent_name: str) -> bool:
        settings = cls.load()
        return tent_name in settings.pid_configs
