import json
import os
import re

from ipaddress import ip_address, AddressValueError
from pydantic import BaseModel, Field, field_validator, IPvAnyAddress
from typing import Optional

SHARED_PATH = os.getenv("SHARED_PATH", "GrowBuddies_shared")
#  -------------- ServicesAddress ----------------
class ServicesAddress(BaseModel):
    '''The services address model is for connecting to the server running the mqtt broker and telegraf services.  To connect, either the hostname or the host_ip must be provided.'''
    name_or_ip: Optional[str] = Field(None, description="Valid hostname or Valid IP address")

    @field_validator('name_or_ip')
    def validate_hostname(cls, name_or_ip):
        '''The hostname must be valid hostname characters (according to the RFC).  It also may not be a string representing an IP address.'''

        # Pattern to identify strings that resemble IP addresses
        # ip_like_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        # Regex pattern for validating a hostname (RFC 1123)
        pattern = r'^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63}(?<!-))*$'
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

        # Check if the hostname matches the pattern
        if re.match(pattern, name_or_ip):
            return name_or_ip
        else:
            raise AddressValueError(f"Invalid hostname or ip address: {name_or_ip}")


    @classmethod
    def load_services_addresses_from_growbuddies_settings(cls):
        '''Load the services addresses from the growbuddies_settings.json file.'''
        with open(f"{SHARED_PATH}/growbuddies_settings.json", "r") as f:
            settings = json.load(f)
            global_settings = settings['global_settings']
            try:
                 # When initializing, pydantic will ignore any extra keys in the dictionary.
                 services_address = cls(**global_settings)
                 return services_address
            except KeyError:
                raise KeyError("host_ip not found within global_settings in growbuddies_settings.json")

#  -------------- MustBuddyLite_state ----------------
class MistBuddyLite_state(ServicesAddress):
    '''Properties specific to running the MistBuddyLite software with a MistBuddy. The state inherits the requirement to have an ip address or hostname to connect to the server running the mqtt broker and telegraf services.'''
    duration_on: float = Field(..., gt=0, le=60, description="Duration in seconds for the mist output from the MistBuddy device. This value is specified during the 'start' endpoint call. Valid range: 1-60 seconds, ensuring misting cycles align with a one-minute interval.")
    name: str = Field(..., description="Specifies the MistBuddy's name, required for the 'start' endpoint call. Utilized for identifying the corresponding MQTT topics for the device.")

    @field_validator('name')
    def validate_name(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty or just whitespace")

        if len(v) > 64: # A bit arbitrary...
            raise ValueError("Name must be 64 characters or less")

        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("Name must contain only alphanumeric characters, underscores, and hyphens")

        return v
