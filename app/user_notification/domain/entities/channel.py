from enum import StrEnum


class Channel(StrEnum):
    """A way to reach a user. A new channel (e.g. WhatsApp) is one more value here
    and one more sender adapter."""

    EMAIL = 'email'
    SMS = 'sms'
