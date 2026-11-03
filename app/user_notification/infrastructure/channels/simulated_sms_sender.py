from app.user_notification.domain.entities.notification import Notification
from app.user_notification.domain.ports.output.channel_sender_port import (
    ChannelSenderPort,
)


class SimulatedSmsSender(ChannelSenderPort):
    """No SMS provider yet (§2): the delivery always succeeds and the use case's log
    is its evidence."""

    async def send(self, notification: Notification) -> None:
        return None
