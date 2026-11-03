from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Self
from uuid import UUID, uuid4

from app.user_notification.domain.entities.channel import Channel
from app.user_notification.domain.entities.notice import Notice


class NotificationStatus(StrEnum):
    PROCESSING = 'processing'
    SENT = 'sent'
    FAILED = 'failed'


@dataclass
class Notification:
    """The record of one notice sent through one channel (one per notice and
    channel). `destination` is a historical copy of the contact used."""

    notice_id: UUID
    user_uuid: UUID
    channel: Channel
    destination: str
    subject: str
    body: str
    created_at: datetime
    updated_at: datetime
    status: NotificationStatus = NotificationStatus.PROCESSING
    attempts: int = 1
    uuid: UUID = field(default_factory=uuid4)

    @classmethod
    def reserve(cls, notice: Notice, channel: Channel, now: datetime) -> Self:
        """The first attempt: the record exists before sending, so a duplicate
        delivery of the notice finds it."""
        return cls(
            notice_id=notice.notice_id,
            user_uuid=notice.recipient.uuid,
            channel=channel,
            destination=notice.destination(channel),
            subject=notice.subject,
            body=notice.body,
            created_at=now,
            updated_at=now,
        )

    @property
    def is_sent(self) -> bool:
        return self.status == NotificationStatus.SENT

    def retry(self, now: datetime) -> None:
        self.status = NotificationStatus.PROCESSING
        self.attempts += 1
        self.updated_at = now

    def mark_sent(self, now: datetime) -> None:
        self.status = NotificationStatus.SENT
        self.updated_at = now

    def mark_failed(self, now: datetime) -> None:
        self.status = NotificationStatus.FAILED
        self.updated_at = now
