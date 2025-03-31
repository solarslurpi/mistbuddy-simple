from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, IPvAnyAddress, field_validator, ValidationInfo, ValidationError
import yaml
from pathlib import Path
import logging

# Get a logger for this module
logger = logging.getLogger(__name__)

# --- Model Definitions to Match YAML Structure ---

class GrowbaseSettings(BaseModel):
    """Settings related to the GrowBase server."""
    host_ip: IPvAnyAddress = Field(..., description="IP address of the GrowBase/MQTT broker")

class MistBuddyDeviceSettings(BaseModel):
    """MQTT topics specific to a MistBuddy device within a tent."""
    mqtt_onoff_topic: str = Field(..., description="Topic to turn misting cycle ON/OFF")
    mqtt_power_topics: List[str] = Field(..., description="List of Tasmota POWER topics for mister/fan")

class LightCheckSettings(BaseModel):
    """Settings for actively querying light status from a designated device using Mem1."""
    light_on_query_topic: str = Field(..., description="Topic to publish to query status on the checker device")
    light_on_response_topic: str = Field(..., description="Topic to listen on for the status RESULT/STATE response")
    light_on_value: Any = Field(..., description="The value indicating lights are ON (e.g., 1, '1')")
    response_timeout: float = Field(..., gt=0, description="Timeout in seconds (>0) to wait for the response")

    @field_validator('light_on_value')
    @classmethod
    def check_on_value_type(cls, v: Any, info: ValidationInfo) -> Any:
        """Check if on_value is likely usable for comparison (int, or str convertible to int)."""
        if isinstance(v, (int, str)):
            try:
                # Check if it can be treated as an int for comparison later
                int(v)
                return v # Return original value (could be str '1')
            except ValueError:
                 raise ValueError(f"Field '{info.field_name}' ('{v}') must be an integer or string representation of an integer")
        raise TypeError(f"Field '{info.field_name}' ('{v}') must be an integer or string; got {type(v)}")

class TentSettings(BaseModel):
    """Configuration for devices within a single tent."""
    MistBuddies: Dict[str, MistBuddyDeviceSettings] = Field(..., description="Dictionary of MistBuddy configurations within the tent, keyed by a unique name/ID")
    LightCheck: LightCheckSettings = Field(..., description="Settings for querying light status")

class AppConfig(BaseModel):
    """Main application configuration model, matching appconfig.yaml structure."""
    # These are the correct top-level fields based on appconfig.yaml
    growbase_settings: GrowbaseSettings
    tents_settings: Dict[str, TentSettings] = Field(..., description="Configuration for each tent, keyed by tent name")

    # --- Convenience Properties/Methods ---

    @property
    def mqtt_broker_ip(self) -> str:
        """Get the IP address of the MQTT broker (derived from GrowBase)."""
        # Convert IPAddress back to string for use with paho-mqtt
        return str(self.growbase_settings.host_ip)

    def get_light_check_settings(self, tent_name: str) -> Optional[LightCheckSettings]:
        """Get LightCheck settings for a specific tent."""
        tent = self.tents_settings.get(tent_name)
        if tent: # Check if tent exists
             # The LightCheck field is mandatory in TentSettings, so we expect it here
             return tent.LightCheck
        logger.warning(f"Tent '{tent_name}' not found in configuration.")
        return None

    def get_mistbuddy_settings(self, tent_name: str, mistbuddy_id: str) -> Optional[MistBuddyDeviceSettings]:
        """Get MistBuddy settings for a specific device in a tent."""
        tent = self.tents_settings.get(tent_name)
        if tent: # Check if tent exists
            mb_settings = tent.MistBuddies.get(mistbuddy_id)
            if mb_settings:
                return mb_settings
            else:
                 logger.warning(f"MistBuddy '{mistbuddy_id}' not found within tent '{tent_name}'.")
                 return None
        logger.warning(f"Tent '{tent_name}' not found in configuration.")
        return None

    # --- Loading Method ---

    @classmethod
    def from_yaml(cls, file_path: Path | str) -> "AppConfig":
        """Load configuration from a YAML file."""
        if isinstance(file_path, str):
            file_path = Path(file_path)

        if not file_path.is_file():
            logger.error(f"Configuration file not found at: {file_path}")
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        logger.info(f"Loading configuration from: {file_path}")
        try:
            with open(file_path, 'r') as file:
                config_data = yaml.safe_load(file)
            if not config_data:
                raise ValueError(f"Configuration file {file_path} is empty or invalid.")
            # Validate data against the Pydantic model
            return cls(**config_data)
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML file {file_path}: {e}", exc_info=True)
            raise ValueError(f"Invalid YAML format in {file_path}") from e
        except ValidationError as e: # Catch Pydantic validation errors specifically
             logger.error(f"Error validating config structure/values from {file_path}:\n{e}", exc_info=False) # Log specific validation errors
             raise ValueError(f"Invalid configuration structure or values in {file_path}") from e
        except Exception as e: # Catch other potential errors during loading/instantiation
            logger.error(f"An unexpected error occurred loading config from {file_path}: {e}", exc_info=True)
            raise ValueError(f"Failed to load configuration from {file_path}") from e

# Note: The old MQTTConfig class has been removed as it's no longer used at the top level.