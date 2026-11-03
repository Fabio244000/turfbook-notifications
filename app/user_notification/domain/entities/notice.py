from dataclasses import dataclass, replace
from uuid import UUID

from app.user_notification.domain.constants import (
    BODY_MAX_LENGTH,
    CELLPHONE_PATTERN,
    EMAIL_MAX_LENGTH,
    EMAIL_MIN_LENGTH,
    EMAIL_PATTERN,
    FIRST_NAME_MAX_LENGTH,
    MAX_CHANNELS,
    MIN_CHANNELS,
    SUBJECT_MAX_LENGTH,
)
from app.user_notification.domain.entities.channel import Channel
from app.user_notification.domain.exceptions import InvalidNoticeError
from app.user_notification.domain.messages import (
    BODY_LENGTH,
    CELLPHONE_INVALID,
    CELLPHONE_REQUIRED,
    CHANNELS_LENGTH,
    EMAIL_INVALID,
    EMAIL_LENGTH,
    EMAIL_REQUIRED,
    FIRST_NAME_LENGTH,
    SUBJECT_LENGTH,
)


@dataclass(frozen=True)
class Recipient:
    uuid: UUID
    email: str | None = None
    cellphone: str | None = None
    first_name: str | None = None


@dataclass
class Notice:
    """The order to notify one user (the contract's notice). It normalizes and
    validates itself as a whole, reporting every failing field at once."""

    notice_id: UUID
    channels: tuple[Channel, ...]
    recipient: Recipient
    subject: str
    body: str

    def __post_init__(self) -> None:
        if self.recipient.email is not None:
            self.recipient = replace(self.recipient, email=self.recipient.email.lower())
        self.subject = self.subject.strip()
        errors = [
            *self._channels_errors(),
            *self._email_errors(),
            *self._cellphone_errors(),
            *self._text_errors(),
        ]
        if errors:
            raise InvalidNoticeError(errors)

    def destination(self, channel: Channel) -> str:
        """The contact the channel uses: the email or the cellphone."""
        destinations = {
            Channel.EMAIL: (self.recipient.email, EMAIL_REQUIRED),
            Channel.SMS: (self.recipient.cellphone, CELLPHONE_REQUIRED),
        }
        value, missing = destinations[channel]
        if value is None:
            raise InvalidNoticeError([missing])
        return value

    def _channels_errors(self) -> list[str]:
        if MIN_CHANNELS <= len(self.channels) <= MAX_CHANNELS:
            return []
        return [CHANNELS_LENGTH]

    def _email_errors(self) -> list[str]:
        email = self.recipient.email
        if email is None:
            return [EMAIL_REQUIRED] if Channel.EMAIL in self.channels else []
        if not EMAIL_MIN_LENGTH <= len(email) <= EMAIL_MAX_LENGTH:
            return [EMAIL_LENGTH]
        return [] if EMAIL_PATTERN.match(email) else [EMAIL_INVALID]

    def _cellphone_errors(self) -> list[str]:
        cellphone = self.recipient.cellphone
        if cellphone is None:
            return [CELLPHONE_REQUIRED] if Channel.SMS in self.channels else []
        return [] if CELLPHONE_PATTERN.match(cellphone) else [CELLPHONE_INVALID]

    def _text_errors(self) -> list[str]:
        first_name = self.recipient.first_name
        errors = []
        if first_name is not None and not 1 <= len(first_name) <= FIRST_NAME_MAX_LENGTH:
            errors.append(FIRST_NAME_LENGTH)
        if not 1 <= len(self.subject) <= SUBJECT_MAX_LENGTH:
            errors.append(SUBJECT_LENGTH)
        if not 1 <= len(self.body) <= BODY_MAX_LENGTH:
            errors.append(BODY_LENGTH)
        return errors
