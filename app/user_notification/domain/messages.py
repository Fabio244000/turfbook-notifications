from app.user_notification.domain.constants import (
    BODY_MAX_LENGTH,
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
NOTIFICATION_ALREADY_RESERVED = (
    'The notice already has a record for this channel (a concurrent delivery).'
)
