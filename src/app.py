import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

# Correct the import statement to use the updated AppConfig model
from src.appconfig import AppConfig, LightCheckSettings, MistBuddyDeviceSettings
# Import the new class location
from src.mistbuddy_simple import MistBuddySimple
# Import the logger setup function (ensure this path is correct)
from src.logger_setup import logger_setup

# Setup root logger using the configuration from logger_setup
# This ensures logging format is applied application-wide
logger_setup('') # Setup root logger
logger = logging.getLogger(__name__) # Get logger for this specific module

def get_config_path() -> Path:
    """Determines the standard path for the user configuration file."""
    home_dir = Path.home()
    # Ensure this directory name is consistent with documentation/setup steps
    app_config_dir_name = "mistbuddy_simple"
    config_dir = home_dir / ".config" / app_config_dir_name
    # Create the directory if it doesn't exist
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "appconfig.yaml"

def main():
    """Entry point - Load config, create instance(s), run application."""
    config: Optional[AppConfig] = None
    config_path: Optional[Path] = None # Define config_path here for broader scope

    try:

        config_path = get_config_path()
        logger.info(f"Attempting to load configuration from user config: {config_path}")

        # Load config using the class method from src.appconfig
        config = AppConfig.from_yaml(config_path)
        logger.info("Configuration loaded successfully.")

        # --- Decide which MistBuddy to run ---
        # TODO: Modify this logic to run multiple instances or use CLI args
        tent_name = 'tent_one'
        mistbuddy_id = 'mistbuddy_1'
        logger.info(f"Targeting MistBuddy '{mistbuddy_id}' in tent '{tent_name}'.")

        # --- Extract settings from the nested config ---
        if tent_name not in config.tents_settings:
            raise KeyError(f"Tent '{tent_name}' not found in configuration.")
        tent_settings = config.tents_settings[tent_name] # Get settings for the whole tent

        if mistbuddy_id not in tent_settings.MistBuddies:
            raise KeyError(f"MistBuddy '{mistbuddy_id}' not found under tent '{tent_name}'.")
        mb_settings: MistBuddyDeviceSettings = tent_settings.MistBuddies[mistbuddy_id] # Get specific MB settings

        # Get required parameters
        broker_ip_val: str = config.mqtt_broker_ip # Use the property to get the string IP
        control_topic_val: str = mb_settings.mqtt_onoff_topic
        power_topics_val: list[str] = mb_settings.mqtt_power_topics
        light_check_settings_obj: LightCheckSettings = tent_settings.LightCheck # Get the LightCheck object for the tent

        logger.info(f"Creating SimpleMistBuddy instance for {tent_name}/{mistbuddy_id}")
        # --- Instantiate MistBuddySimple with ALL required parameters ---
        buddy = MistBuddySimple(
            broker_ip=broker_ip_val,
            control_topic=control_topic_val,
            power_topics=power_topics_val,
            light_check_settings=light_check_settings_obj # Pass the full LightCheckSettings object
        )

        logger.info(f"Successfully initialized MistBuddy '{mistbuddy_id}' in tent '{tent_name}'. Starting run loop.")
        # Now run the application's async part
        asyncio.run(buddy.run())

    except FileNotFoundError:
        logger.critical(f"CRITICAL: Configuration file NOT FOUND at expected location: '{config_path}'. Please create it.")
        sys.exit(1)
    except (KeyError, ValueError, AttributeError) as e: # Catch config structure/validation/access errors
         logger.critical(f"CRITICAL: Configuration Error - {e}")
         # Optionally log more details if needed, e.g., logger.debug("Config object state:", config)
         sys.exit(1)
    except ConnectionError as e: # Catch connection errors during MistBuddy init
         logger.critical(f"CRITICAL: Connection Setup Error - {e}", exc_info=False) # Log specific error message
         sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received. Shutting down.")
        # Allow finally block to handle cleanup
    except Exception as e:
        logger.critical(f"CRITICAL: An unexpected error occurred in main: {e}", exc_info=True)
        sys.exit(1) # Exit on other critical errors
    finally:
        logger.info("Application finished.")


if __name__ == "__main__":
    main()