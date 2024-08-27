from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Dict, List, Optional

class GlobalSettings(BaseModel):
    hostname: str
    host_ip: str
    db_name: str

class PIDConfig(BaseModel):
    active: bool
    setpoint: float
    Kp: float
    Ki: float
    Kd: float
    output_limits: List[float]
    integral_limits: List[float]
    tune_start: int
    tune_increment: int
    comparison_function: str
    mqtt_power_topics: List[str]
    telegraf_fieldname: str
    num_bias_seconds_on: int

class TentConfig(BaseModel):
    MistBuddy: PIDConfig
    CO2Buddy: PIDConfig

class GrowBuddiesSettings(BaseSettings):
    global_settings: GlobalSettings = Field(default_factory=lambda: GlobalSettings(
        hostname="gus.local",
        host_ip="192.168.68.113",
        db_name="gus",
    ))
    pid_configs: Dict[str, TentConfig] = Field(default_factory=lambda: {
        "tent_one": TentConfig(
            MistBuddy=PIDConfig(
                active=True,
                setpoint=1.0,
                Kp=100.0,
                Ki=0.8,
                Kd=5,
                output_limits=[0, 50],
                integral_limits=[0, 30],
                tune_start=0,
                tune_increment=0,
                comparison_function="less_than",
                mqtt_power_topics=["cmnd/mistbuddy_fan/POWER", "cmnd/mistbuddy_mister/POWER"],
                telegraf_fieldname="vpd_mean",
                num_bias_seconds_on=20
            ),
            CO2Buddy=PIDConfig(
                active=False,
                setpoint=1000,
                Kp=0.1,
                Ki=0.01,
                Kd=0.01,
                output_limits=[0, 15],
                integral_limits=[0, 12],
                tune_start=0,
                tune_increment=0,
                comparison_function="greater_than",
                mqtt_power_topics=["cmnd/stomabuddy/POWER"],
                telegraf_fieldname="CO2_mean",
                num_bias_seconds_on=0
            )
        )
    })

# Create an instance of the settings
settings = GrowBuddiesSettings()

# Helper function to get a specific tent's configuration
def get_tent_config(tent_name: str) -> Optional[TentConfig]:
    return settings.pid_configs.get(tent_name)

# Helper function to check if a tent name is valid
def is_valid_tent_name(tent_name: str) -> bool:
    return tent_name in settings.pid_configs

# Helper function to get all tent names
def get_all_tent_names() -> List[str]:
    return list(settings.pid_configs.keys())

# Helper function to get power settings for a specific tent and device
def get_power_settings(tent_name: str, device_type: str) -> List[str]:
    tent_config = get_tent_config(tent_name)
    if tent_config and device_type in ["MistBuddy", "CO2Buddy"]:
        device_config = getattr(tent_config, device_type)
        return device_config.mqtt_power_topics
    return []

# Example usage:
# if __name__ == "__main__":
#     print(f"Global settings: {settings.global_settings}")
#     print(f"Tent names: {get_all_tent_names()}")
#     print(f"Tent One MistBuddy config: {get_tent_config('tent_one').MistBuddy}")
