import yaml
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, IPvAnyAddress
from pydantic_settings import BaseSettings

class GrowBaseSettings(BaseModel):
    host_ip: Optional[IPvAnyAddress] = None

class BuddySettings(BaseModel):
    mqtt_power_topics: List[str]

class TentSettings(BaseModel):
    MistBuddy: BuddySettings
    CO2Buddy: BuddySettings

class AppSettings(BaseSettings):
    growbase_settings: GrowBaseSettings = Field(default_factory=GrowBaseSettings)
    tents_settings: Dict[str, TentSettings] = Field(default_factory=dict)

class Config:
    _instance = None
    settings: AppSettings = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance

    @classmethod
    def load_settings(cls, config_file: str):
        with open(config_file, 'r') as file:
            yaml_data = yaml.safe_load(file)
        cls._instance.settings = AppSettings(**yaml_data)
        return cls._instance.settings

    @classmethod
    def get_settings(cls) -> AppSettings:
        if cls._instance is None or cls._instance.settings is None:
            raise RuntimeError("Settings not loaded. Call load_settings first.")
        return cls._instance.settings

    @classmethod
    def is_valid_tent_name(cls, tent_name: str) -> bool:
        return tent_name in cls.get_settings().tents_settings

    @classmethod
    def get_host_ip(cls) -> IPvAnyAddress:
        return cls.get_settings().growbase_settings.host_ip.compressed


    @classmethod
    def get_tent_settings(cls, tent_name: str) -> Optional[TentSettings]:
        return cls.get_settings().tents_settings.get(tent_name)

    @classmethod
    def get_power_topics(cls, tent_name: str, device_type: str) -> List[str]:
        tent_settings = cls.get_tent_settings(tent_name)
        if tent_settings and device_type in ["MistBuddy", "CO2Buddy"]:
            return getattr(tent_settings, device_type).mqtt_power_topics
        return []

# Global instance
config = Config()
