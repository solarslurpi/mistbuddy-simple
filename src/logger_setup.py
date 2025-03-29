import logging
import logging.config
from src.logging_config import LOGGING_CONFIG

def logger_setup(name: str) -> logging.Logger:
    logging.config.dictConfig(LOGGING_CONFIG)
    return logging.getLogger(name)