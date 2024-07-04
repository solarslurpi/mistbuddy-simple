import re

def validate_hostname(hostname):

    # Regex pattern for RFC 1123 hostname validation
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
    if re.match(pattern, hostname):
        return True

    return False

# Test cases
label_64 = 'a123456701234567012345670123456701234567012345670123456701234567'
test_cases = [
    ('123.456', True), # hostnames can contain letters, digits, or numbers.
    ('😺', False), # hostnames cannot contain special characters.
    ('01010', True), # hostnames can contain letters, digits, or numbers.
    ('0.1.0.3', True), # hostnames can contain letters, digits, or numbers.
    ('abc', True), # hostnames can contain letters, digits, or numbers.
    ('A0c', True), # hostnames can contain letters, digits, or numbers.
    ('A0c-', False), # hostnames cannot end with a dash
    ('-A0c', False), # hostnames cannot start with a dash
    ('A-0c', True), # (consecutive) dashes are allowed in the middle of the hostname
    (label_64, False), # While a domain name is a hostname which can be up to 255 characters long, a part of the domain name (label) can be up to 63 characters long.
    ('o12345670123456701234567012345670123456701234567012345670123456', True),
    ('', False), # hostnames cannot be empty
    ('a', True), # hostnames must be at least one character.
    ('0--0', True), # (consecutive) dashes are allowed in the middle of the hostname,
]

# Run tests
print(len(label_64))
for hostname, expected in test_cases:
    result = validate_hostname(hostname)
    print(f"Hostname: {hostname}, Expected: {expected}, Result: {result}")