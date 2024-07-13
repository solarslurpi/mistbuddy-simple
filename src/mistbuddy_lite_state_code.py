import json
import logging
import os
import re
from json import JSONDecodeError
from typing import Optional

from fastapi import HTTPException
from ipaddress import ip_address, AddressValueError
from pydantic import BaseModel, Field, field_validator, PrivateAttr

from logger_code import LoggerBase

logger = LoggerBase.setup_logger("MistBuddyLite", logging.DEBUG)

SHARED_PATH = os.getenv("SHARED_PATH", "GrowBuddies_shared")
#  -------------- ServicesAddress ----------------
class ServicesAddress(BaseModel):
    '''
    The ServicesAddress model holds the ip address or name of the host that is running services such as an mqtt broker and telegraf. It is loaded from growbuddies_settings.json
    '''
    address: Optional[str] = Field(None, description="Valid hostname or IP address that will be read in by growbuddies_settings.json.")

    @field_validator('address')
    def validate_address(address: str) -> str:
        # Pattern to identify strings that resemble IP addresses
        # ip_like_pattern = r'^(\d{1,3}\.){1,3}\d{1,3}$'
        # Regex pattern for validating a hostname (RFC 1123)
        # Regex pattern for RFC 1123 hostname validation (which includes ip addresses)
        rfc1123_pattern = r'^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63}(?<!-))*$'
        # ^(?=.{1,253}$):
        #   ^: Asserts the position at the start of the string.
        #   (?=.{1,253}$): Positive lookahead to ensure the entire string length is between 1 and 253 characters.
        # (?!-)[A-Za-z0-9-]{1,63}(?<!-)
        #   (?!-): A label (within the hostname) must not start with a dash.
        #   [A-Za-z0-9-]{1,63}: A label can contain letters (A-Z, a-z), digits (0-9), and hyphens (-). It can be up to 63 characters long.
        # (?<!-): A label (within the hostname) must not end with a dash.
        # (\.
        #   The hostname can have multiple labels separated by a dot (.),
        # [A-Za-z0-9-]{1,63}(?<!-))*$
        #   Each label can be up to 63 characters long.
        if not re.match(rfc1123_pattern, address):
            raise AddressValueError(f"Invalid hostname: {address}")
        # Check if the address is an IP address
        ip_like_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if re.match(ip_like_pattern, address):
            # The string resembles an IP address, check if it is a valid one.
            try:
                ip_address(address)
            except AddressValueError:
                raise AddressValueError(f"Invalid IP address: {address}")
        return address

class PowerMessages(BaseModel):
    power_messages: Optional[list[str]] = Field(None, min_length=2, max_length=2, description="List of MQTT topics for the power switches associated with the MistBuddy device.")

    @field_validator('power_messages')
    def validate_power_messages(cls, v):
        '''The power messages are sent to Tasmota devices. Tasmota uses the schema: cmnd/<device_name>/POWER. The MistBuddy device has 2 power switches: one for the fan and one for the mister. The power messages must be a list with exactly 2 elements. The check to make sure there are only 2 elements is done in the field_validator. This function checks that the elements are in the correct format.'''
        if len(v) != 2:
            raise ValueError("Power messages must contain exactly 2 elements.")


        for message in v:

            # If the last text after the last '/' is not 'POWER', but not in uppercase, make all characters uppercase.
            if message.split('/')[-1].upper() != 'POWER':
                message = '/'.join(message.split('/')[:-1]) + '/POWER'
            cls.match_power_message_or_raise_error(message)
        return v

    @classmethod
    def match_power_message_or_raise_error(cls, power_message:str):
        tasmota_command_pattern = r'^cmnd\/[a-zA-Z0-9_-]+\/POWER$'
        if not re.match(tasmota_command_pattern, power_message):
            raise ValueError(f"Power message '{power_message}' does not match the expected Tasmota command")
        return power_message

class UserInput(BaseModel):
    '''Properties specific to running the MistBuddyLite software with a MistBuddy.'''
    duration_on: float = Field(..., gt=0, le=60, description="Duration in seconds for the mist output from the MistBuddy device.")
    name: str = Field(..., description="Specifies the MistBuddy's name.")

    @field_validator('duration_on')
    def validate_duration_on(cls, v):
        if not isinstance(v, (int, float)):  # Accept both integers and floats
            raise ValueError("Duration must be a number.")
        if v <= 0:  # Assuming duration must be greater than 0
            raise ValueError("Duration must be greater than 0.")
        return v

    @field_validator('name')
    def validate_name(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty or just whitespace")

        if len(v) > 64: # A bit arbitrary...
            raise ValueError("Name must be 64 characters or less")

        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("Name must contain only alphanumeric characters, underscores, and hyphens.")

        return v
# -------------- MistBuddyLiteState ----------------
class MistBuddyLiteState(UserInput, ServicesAddress, PowerMessages):
    pass

class MistBuddyLiteStateSingleton:
    _instance = None

    @classmethod
    def get_mistbuddy_state(cls, user_input: UserInput):
        if cls._instance is None:
            logger.debug("Creating a new instance of MistBuddyLiteState.")
            try:
                settings = cls.load_growbuddies_settings()
                services_address = ServicesAddress(**settings['global_settings'])
                power_messages = settings['mqtt_power_messages'][user_input.name]['mistbuddy']
                cls._instance = MistBuddyLiteState(
                    name=user_input.name,
                    duration_on=user_input.duration_on,
                    address=services_address.address,
                    power_messages=power_messages
                )
            except FileNotFoundError:
                logger.debug("growbuddies_settings.json file not found.")
                raise
            except json.JSONDecodeError:
                logger.debug("Error decoding growbuddies_settings.json. Please check the file format.")
                raise
            except KeyError as e:
                logger.debug(f"KeyError: {e}")
                raise
            except Exception as e:
                logger.debug(f"An unexpected error occurred: {e}")
                raise

        return cls._instance

    @classmethod
    def load_growbuddies_settings(cls):
        '''Load the services addresses from the growbuddies_settings.json file.'''
        settings = None
        file_path = os.path.join(SHARED_PATH, "growbuddies_settings.json")
        try:
            with open(file_path, "r") as f:
                settings = json.load(f)
                return settings
        except FileNotFoundError:
            raise FileNotFoundError(f"Settings file: {file_path} not found.")
