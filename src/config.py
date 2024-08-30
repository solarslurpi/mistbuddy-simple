from pydantic import BaseModel, Field, ConfigDict
from pydantic_settings import BaseSettings
from typing import Dict, List, Optional

class GrowBaseSettings(BaseModel):
    hostname: str
    host_ip: str

class BuddySettings(BaseModel):
    mqtt_power_topics: List[str]

class TentSettings(BaseModel):
    MistBuddy: BuddySettings
    CO2Buddy: BuddySettings

class Settings(BaseSettings):
    model_config = ConfigDict(env_nested_delimiter='__')

    growbase_settings: GrowBaseSettings
    tents_settings: Dict[str, TentSettings] = Field(default_factory=dict, description="Tent settings")

default_settings = {
    "growbase_settings": {
        "hostname": "gus.local",
        "host_ip": "192.168.68.113",
    },
    "tents_settings": {
        "tent_one": {
            "MistBuddy": {
                "mqtt_power_topics": [
                    "cmnd/mistbuddy_fan/POWER",
                    "cmnd/mistbuddy_mister/POWER"
                    ],
            },
            "CO2Buddy": {
                "mqtt_power_topics": [
                    "cmnd/stomabuddy/POWER"
                    ],
            }
        }
    }
}

# Create settings instance with default values
settings = Settings(**default_settings)

# Helper function to get the host IP
def get_host_ip():
    return settings.growbase_settings.host_ip
# Helper function to get a specific tent's configuration
def get_tent_settings(tent_name: str) -> Optional[TentSettings]: # Will return None if the key is not found.
    # tents_settings is a dictionary where the key is the tent name
    return settings.tents_settings.get(tent_name)

# Helper function to check if a tent name is valid
def is_valid_tent_name(tent_name: str) -> bool:
    return tent_name in settings.tents_settings

# Helper function to get all tent names
def get_all_tent_names() -> List[str]:
    return list(settings.tents_settings.keys())

# Helper function to get power settings for a specific tent and device
def get_power_settings(tent_name: str, device_type: str) -> List[str]:
    tent_settings = get_tent_settings(tent_name)
    if tent_settings and device_type in ["MistBuddy", "CO2Buddy"]:
        return tent_settings.MistBuddy.mqtt_power_topics
    return []

# Example usage:
if __name__ == "__main__":
    print(f"GrowBase settings: {settings.growbase_settings}")
    print(f"Tent names: {get_all_tent_names()}")
    print(f"Tent One MistBuddy config: {get_tent_settings('tent_one').MistBuddy}")
