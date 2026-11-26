import re

MIN_CHANNELS = 1
MAX_CHANNELS = 2
EMAIL_PATTERN = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
EMAIL_MIN_LENGTH = 6
EMAIL_MAX_LENGTH = 254
CELLPHONE_PATTERN = re.compile(r'^\+519[0-9]{8}$')
FIRST_NAME_MAX_LENGTH = 250
SUBJECT_MAX_LENGTH = 250
BODY_MAX_LENGTH = 4000
# Security code: six digits, placed in the body by a placeholder, and masked in
# everything that is recorded or logged.
CODE_PATTERN = re.compile(r'^[0-9]{6}$')
CODE_PLACEHOLDER = '{code}'
CODE_MASK = '******'
