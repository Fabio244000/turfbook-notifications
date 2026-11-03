from abc import ABC, abstractmethod

from app.user_notification.domain.entities.notification import Notification


class ChannelSenderPort(ABC):
    """Delivers a notification through one channel (email, SMS…)."""

    @abstractmethod
    async def send(self, notification: Notification) -> None:
        """Raises `DeliveryRejectedError` when the channel refuses it for good and
        `DeliveryUnavailableError` when it cannot take it now."""
