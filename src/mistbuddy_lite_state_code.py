import json
import os
import re
from typing import Optional

from ipaddress import ip_address, AddressValueError
from pydantic import BaseModel, Field, field_validator

SHARED_PATH = os.getenv("SHARED_PATH", "GrowBuddies_shared")
#  -------------- ServicesAddress ----------------
class ServicesAddress(BaseModel):
    '''
    The ServicesAddress model holds the ip address or name of the host that is running services such as an mqtt broker and telegraf.
    '''
    address: str = Field(..., description="Valid hostname or IP address")

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

        # The hostname is valid, check if it can be resolved.
        # This might be too much.
        # try:
        #     # Try to resolve the hostname
        #     socket.gethostbyname(address)
        #     return address
        # except socket.error:
        #     raise AddressValueError('Hostname could not be resolved.')



# -------------- MistBuddyLite_state ----------------
class MistBuddyLite_state(ServicesAddress):
    '''Properties specific to running the MistBuddyLite software with a MistBuddy.'''
    duration_on: float = Field(..., gt=0, le=60, description="Duration in seconds for the mist output from the MistBuddy device.")
    name: str = Field(..., description="Specifies the MistBuddy's name.")
    power_messages: Optional[list[str]] =  Field(None, min_length=2, max_length=2, description="List of MQTT topics for the power switches associated with the MistBuddy device.")

#  -------------- MustBuddyLite_state ----------------
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

    @field_validator('duration_on')
    def validate_duration_on(cls, v):
        if not isinstance(v, (int, float)):  # Accept both integers and floats
            raise ValueError("Duration must be a number.")
        if v <= 0:  # Assuming duration must be greater than 0
            raise ValueError("Duration must be greater than 0.")
        return v

    @field_validator('power_messages')
    def validate_power_messages(cls, v):
        '''The power messages are sent to Tasmota devices.  Tasmota uses the schema: cmnd/<device_name>/POWER.  The MistBuddy device has 2 power switches: one for the fan and one for the mister.  The power messages must be a list with exactly 2 elements. The check to make sure there are only 2 elements is done in the field_validator.  This function checks that the elements are in the correct format.'''
        tasmota_command_pattern = r'^cmnd\/[a-zA-Z0-9_-]+\/POWER$'
        for message in v:
            if not re.match(tasmota_command_pattern, message):
                raise ValueError(f"Power message '{message}' does not match the expected Tasmota command format 'cmnd/<device_name>/POWER'")
        return v

    @classmethod
    def load_growbuddies_settings(cls, file_path):
        '''Load the services addresses from the growbuddies_settings.json file.'''
        try:
            with open(file_path, "r") as f:
                settings = json.load(f)
                return settings

        except FileNotFoundError:
            raise FileNotFoundError(f"Settings file: {file_path} not found.")
