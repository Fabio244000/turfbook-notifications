from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID

from app.user_notification.domain.entities.channel import Channel


@dataclass(frozen=True)
class SendNoticeCommand:
    """The notice as it arrives, already structurally valid (types, enum values)."""

    notice_id: UUID
    channels: tuple[Channel, ...]
    recipient_uuid: UUID
    subject: str
    body: str
    email: str | None = None
    cellphone: str | None = None
    first_name: str | None = None


class SendNoticePort(ABC):
    @abstractmethod
    async def execute(self, command: SendNoticeCommand) -> None:
        """Sends the notice once per channel and records each delivery.

        Raises `InvalidNoticeError` for a malformed notice and
        `DeliveryUnavailableError` when a channel must be retried.
        """
