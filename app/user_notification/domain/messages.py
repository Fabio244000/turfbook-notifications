from app.user_notification.domain.constants import (
    BODY_MAX_LENGTH,
    CODE_PLACEHOLDER,
    EMAIL_MAX_LENGTH,
    EMAIL_MIN_LENGTH,
    FIRST_NAME_MAX_LENGTH,
    MAX_CHANNELS,
    MIN_CHANNELS,
    SUBJECT_MAX_LENGTH,
)

CHANNELS_LENGTH = f'channels must have between {MIN_CHANNELS} and {MAX_CHANNELS} items.'
EMAIL_REQUIRED = 'email is required for the email channel.'
EMAIL_INVALID = 'email is invalid.'
EMAIL_LENGTH = (
    f'email must have between {EMAIL_MIN_LENGTH} and {EMAIL_MAX_LENGTH} characters.'
)
CELLPHONE_REQUIRED = 'cellphone is required for the sms channel.'
CELLPHONE_INVALID = 'cellphone is invalid.'
FIRST_NAME_LENGTH = (
    f'first_name must have between 1 and {FIRST_NAME_MAX_LENGTH} characters.'
)
SUBJECT_LENGTH = f'subject must have between 1 and {SUBJECT_MAX_LENGTH} characters.'
BODY_LENGTH = f'body must have between 1 and {BODY_MAX_LENGTH} characters.'
CODE_INVALID = 'code is invalid.'
CODE_PLACEHOLDER_REQUIRED = (
    f'body must contain {CODE_PLACEHOLDER} exactly once when there is a code.'
)
CODE_PLACEHOLDER_WITHOUT_CODE = (
    f'body cannot contain {CODE_PLACEHOLDER} without a code.'
)
SUBJECT_WITH_CODE_PLACEHOLDER = f'subject cannot contain {CODE_PLACEHOLDER}.'
NOTIFICATION_ALREADY_RESERVED = (
    'The notice already has a record for this channel (a concurrent delivery).'
)
