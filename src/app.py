import asyncio
from pathlib import Path
from typing import Optional
import logging # Use standard logging

# Correct the import statement to use the new filename
from src.appconfig import AppConfig, MistBuddyDeviceSettings
# Import the new class location
from src.mistbuddy_simple import SimpleMistBuddy 
# Import the logger setup function
from src.logger_setup import logger_setup 

# Setup root logger using the configuration from logger_setup
# This ensures logging format is applied application-wide
logger_setup('') # Setup root logger
logger = logging.getLogger(__name__) # Get logger for this specific module


def main():
    """Entry point - Load config, create instance(s), run application."""
    config: Optional[AppConfig] = None
    try:
        # Define config path relative to the project root
        project_root = Path(__file__).parent
        config_path = project_root / 'appconfig.yaml'

        # Load config using the class method from src.appconfig
        config = AppConfig.from_yaml(config_path)

        # --- Decide which MistBuddy to run ---
        # TODO: Modify this logic to run multiple instances if needed
        tent_name = 'tent_one'
        mistbuddy_id = 'mistbuddy_1'

        mistbuddy_settings: Optional[MistBuddyDeviceSettings] = None
        if tent_name in config.tents_settings:
            tent = config.tents_settings[tent_name]
            if mistbuddy_id in tent.MistBuddies:
                 mistbuddy_settings = tent.MistBuddies[mistbuddy_id]

        if not mistbuddy_settings:
             logger.critical(f"MistBuddy settings for '{mistbuddy_id}' in tent '{tent_name}' not found in config.")
             raise ValueError(f"Missing config for {tent_name}/{mistbuddy_id}")

        # Create the SimpleMistBuddy instance with specific config values
        logger.info(f"Creating SimpleMistBuddy instance for {tent_name}/{mistbuddy_id}")
        buddy = SimpleMistBuddy(
            broker_ip=config.mqtt_broker_ip,
            control_topic=mistbuddy_settings.mqtt_onoff_topic,
            power_topics=mistbuddy_settings.mqtt_power_topics
        )

        # Now run the application's async part
        asyncio.run(buddy.run())

    except FileNotFoundError:
        logger.critical(f"CRITICAL: Configuration file '{config_path}' not found.")
    except (KeyError, ValueError, AttributeError, ConnectionError) as e: # Added ConnectionError
         logger.critical(f"CRITICAL: Setup Error - {e}", exc_info=True)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received. Shutting down.")
    except Exception as e:
        logger.error(f"Fatal unexpected error in main: {e}", exc_info=True)

    logger.info("Application finished.")


if __name__ == "__main__":
    main()