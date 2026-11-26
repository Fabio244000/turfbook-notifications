from app.user_notification.domain.entities.outgoing_message import OutgoingMessage
from app.user_notification.domain.ports.output.channel_sender_port import (
    ChannelSenderPort,
)


class SimulatedSmsSender(ChannelSenderPort):
    """No SMS provider yet: the delivery always succeeds and the use case's log
    is its evidence."""

    async def send(self, message: OutgoingMessage) -> None:
        return None
