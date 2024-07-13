import pytest

from mistbuddy_lite_state_code import ServicesAddress, MistBuddyLiteState


@pytest.mark.parametrize("hostname,expected", [
    ("192.168.1.1", True),
    ("256.256.256.256", False),
    ("1.1.1.1.1", True),
    ("frank", True),
    ("", False),
    ("😺", False),
    ('123.456', True),
    ('01010', True),
    ('abc', True),
    ('A0c', True),
    ('A0c-', False),
    ('-A0c', False),
    ('A-0c', True),
    ('o123456701234567012345670123456701234567012345670123456701234567', False),
    ('o12345670123456701234567012345670123456701234567012345670123456', True),
    ('', False),
    ('a', True),
    ('0--0', True),
])
def test_validate_hostname_or_ip(hostname, expected):
    ''''Test the list of host names and IP addresses to see if whether they are valid are not make sense based on RFC 1123 (hostname) and IP address rules.'''
    if expected:
        assert ServicesAddress.validate_address(hostname) == hostname
    else:
        with pytest.raises(ValueError):
            ServicesAddress.validate_address(hostname)

@pytest.mark.parametrize("message, expected", [
    (["cmnd/tent_one_mistbuddy_fan/POWER","cmnd/tent_one_mistbuddy_fan/POWER"], True),
    ("cmnd/mistbuddy_in_second_room/POWER", False), # Only one message.
    (["cmd/device1/POWER","cmdn/foo/POWER"], False), # cmd and cmdn are incorrect.
    # ("cmnd//POWER", False),
    # ("cmnd/device1/power", False),
    # ("cmnd/device1/pwr", False),
    (["cmnd/😺/POWER", "cmnd/tent_one_mistbuddy_fan/POWER"],False), # No special characters.
    (["123","rgg"], False), # Must be Tasmota command format.
    # ("", False)
])
def test_validate_power_messages(message, expected):
    if expected:
        assert MistBuddyLiteState.validate_power_messages(message) == message
    else:
        with pytest.raises(ValueError) as excinfo:
            MistBuddyLiteState.validate_power_messages(message)


def test_load_growbuddies_settings():
    '''Use the growbuddies_settings fixture (see conftest.py) to load the settings and test the load_state_from_growbuddies_settings method.'''

    result = MistBuddyLite_state.load_growbuddies_settings()

    # Validate the result against the expected content
    assert result['global_settings']['address'] == "192.168.68.113"
    assert result['mqtt_power_messages'] == {
        "tent_one": {"mistbuddy":["cmnd/tent_one_mistbuddy_fan/POWER", "cmnd/tent_one_mistbuddy_mister/POWER"],"co2buddy":["cmnd/tent_one_co2buddy/POWER"]}
    }

@pytest.mark.parametrize("name, is_valid, duration_on", [
    ("ValidName123", True, 10), # A valid name
    ("Invalid Name With Spaces", False, 10),
    ("AnotherValidName", True, 5.5),
    ("AnotherValidName", False, 'one and a half'),  # Pydantic can't coerce to number...
    ("", False, 5),  # Assuming an empty string is invalid
    ("123456", False, 0),  # Duration must be greater than 0.
    ("$$$$$", False, 10),  # Assuming an invalid name
    ("NameWithSpecialChar$%", False, 10),  # Assuming special characters are invalid
    ("valid", True, "58"), # Duration must be an integer between 1 and 60. When possible, Pydantic coerces the string into the correct type (which is a float in this case).
    ("valid", False, "invalid") #Pydantic can't coerce to number...
])

def test_mistbuddy_lite_state_validation(name, is_valid, duration_on):
    '''Tests the validation of the MistBuddyLite_state object. Specifically, it verifies that the 'name' and 'duration_on' properties are correctly validated according to the provided rules. This ensures that only valid requests to the start endpoint initiate misting.'''
    if is_valid:
        instance = MistBuddyLiteState(address="192.168.68.113", name=name, duration_on=duration_on)
        assert instance.name == name, "The name should be valid and correctly set."
        # Convert duration_on to float if it's a string or int that represents a number
        duration_as_float = float(duration_on) if isinstance(duration_on, str) and duration_on.replace('.', '', 1).isdigit() else duration_on
        assert instance.duration_on == duration_as_float, "The duration_on should be correctly set."

    else:
        with pytest.raises(ValueError):
            MistBuddyLiteState(address="192.168.1.1", name=name, duration_on=duration_on)
