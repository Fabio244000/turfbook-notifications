from abc import ABC, abstractmethod

from app.user_notification.domain.entities.outgoing_message import OutgoingMessage


class ChannelSenderPort(ABC):
    """Delivers a message through one channel (email, SMS…)."""

    @abstractmethod
    async def send(self, message: OutgoingMessage) -> None:
        """Raises `DeliveryRejectedError` when the channel refuses it for good and
        `DeliveryUnavailableError` when it cannot take it now."""
