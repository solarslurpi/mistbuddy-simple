from typing import Dict, List, Optional
from pydantic import BaseModel, Field, IPvAnyAddress
import yaml
from pathlib import Path
import logging

# Get a logger for this module
logger = logging.getLogger(__name__)

class GrowbaseSettings(BaseModel):
    """Settings related to the GrowBase server."""
    host_ip: IPvAnyAddress # Use IPvAnyAddress for validation

class MistBuddyDeviceSettings(BaseModel):
    """MQTT topics specific to a MistBuddy device within a tent."""
    mqtt_onoff_topic: str = Field(..., description="Topic to turn misting cycle ON/OFF")
    mqtt_power_topics: List[str] = Field(..., description="List of Tasmota POWER topics for mister/fan")

class TentSettings(BaseModel):
    """Configuration for devices within a single tent."""
    MistBuddies: Dict[str, MistBuddyDeviceSettings] = Field(..., description="Dictionary of MistBuddy configurations within the tent, keyed by a unique name/ID")

class AppConfig(BaseModel):
    """Main application configuration model."""
    growbase_settings: GrowbaseSettings
    tents_settings: Dict[str, TentSettings] = Field(..., description="Configuration for each tent, keyed by tent name")

    # --- Convenience Properties/Methods ---

    @property
    def mqtt_broker_ip(self) -> str:
        """Get the IP address of the MQTT broker (GrowBase)."""
        # Convert IPAddress back to string for use with paho-mqtt
        return str(self.growbase_settings.host_ip) 

    def get_mistbuddy_settings(self, tent_name: str) -> Optional[MistBuddyDeviceSettings]:
        """Get MistBuddy settings for a specific tent."""
        tent = self.tents_settings.get(tent_name)
        if tent:
            return tent.MistBuddy
        logger.warning(f"No settings found for tent: {tent_name}")
        return None

    # --- Loading Method ---

    @classmethod
    def from_yaml(cls, file_path: Path | str):
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
            # Validate data against the Pydantic model
            return cls(**config_data) 
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML file {file_path}: {e}", exc_info=True)
            raise ValueError(f"Invalid YAML format in {file_path}") from e
        except Exception as e: # Catch Pydantic validation errors too
            logger.error(f"Error loading or validating config from {file_path}: {e}", exc_info=True)
            raise ValueError(f"Invalid configuration structure in {file_path}") from e

