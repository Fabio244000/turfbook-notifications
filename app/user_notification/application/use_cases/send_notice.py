import logging
from collections.abc import Mapping
from datetime import datetime

from app.user_notification.application.messages import (
    DELIVERY_LOG,
    RESULT_REJECTED,
    RESULT_SENT,
    RESULT_UNAVAILABLE,
)
from app.user_notification.domain.entities.channel import Channel
from app.user_notification.domain.entities.notice import Notice, Recipient
from app.user_notification.domain.entities.notification import Notification
from app.user_notification.domain.exceptions import (
    DeliveryRejectedError,
    DeliveryUnavailableError,
)
from app.user_notification.domain.ports.input.send_notice_port import (
    SendNoticeCommand,
    SendNoticePort,
)
from app.user_notification.domain.ports.output.channel_sender_port import (
    ChannelSenderPort,
)
from app.user_notification.domain.ports.output.clock_port import ClockPort
from app.user_notification.domain.ports.output.unit_of_work_port import UnitOfWorkPort

logger = logging.getLogger(__name__)

MASK = '***'


class SendNoticeUseCase(SendNoticePort):
    """Sends a notice once per channel. Each channel is reserved (committed) before
    sending and marked after, so a duplicate or a retry never resends a channel
    already sent; a temporary failure is raised only after every channel ran."""

    def __init__(
        self,
        uow: UnitOfWorkPort,
        senders: Mapping[Channel, ChannelSenderPort],
        clock: ClockPort,
    ) -> None:
        self._uow = uow
        self._senders = senders
        self._clock = clock

    async def execute(self, command: SendNoticeCommand) -> None:
        notice = _notice(command)
        now = self._clock.now()
        unavailable: DeliveryUnavailableError | None = None
        for channel in dict.fromkeys(notice.channels):
            try:
                await self._deliver(notice, channel, now)
            except DeliveryUnavailableError as error:
                unavailable = error
        if unavailable is not None:
            raise unavailable

    async def _deliver(self, notice: Notice, channel: Channel, now: datetime) -> None:
        notification = await self._reserve(notice, channel, now)
        if notification is None:
            return
        try:
            await self._senders[channel].send(notification)
        except DeliveryRejectedError as error:
            await self._finish(notification, now, sent=False)
            _log(notification, RESULT_REJECTED, error)
            return
        except DeliveryUnavailableError as error:
            await self._finish(notification, now, sent=False)
            _log(notification, RESULT_UNAVAILABLE, error)
            raise
        await self._finish(notification, now, sent=True)
        _log(notification, RESULT_SENT)

    async def _reserve(
        self, notice: Notice, channel: Channel, now: datetime
    ) -> Notification | None:
        """The channel's record in `processing`, or None when it was already sent."""
        async with self._uow as uow:
            notification = await uow.notifications.get(notice.notice_id, channel)
            if notification is not None and notification.is_sent:
                return None
            if notification is None:
                notification = Notification.reserve(notice, channel, now)
                await uow.notifications.add(notification)
            else:
                notification.retry(now)
                await uow.notifications.update(notification)
            await uow.commit()
        return notification

    async def _finish(
        self, notification: Notification, now: datetime, *, sent: bool
    ) -> None:
        async with self._uow as uow:
            if sent:
                notification.mark_sent(now)
            else:
                notification.mark_failed(now)
            await uow.notifications.update(notification)
            await uow.commit()


def _notice(command: SendNoticeCommand) -> Notice:
    return Notice(
        notice_id=command.notice_id,
        channels=command.channels,
        recipient=Recipient(
            uuid=command.recipient_uuid,
            email=command.email,
            cellphone=command.cellphone,
            first_name=command.first_name,
        ),
        subject=command.subject,
        body=command.body,
    )


def _masked(channel: Channel, destination: str) -> str:
    """Hides a contact for the log: `l***@gmail.com`, `+51***321`."""
    if channel is Channel.EMAIL:
        local, _, domain = destination.partition('@')
        return f'{local[:1]}{MASK}@{domain}'
    return f'{destination[:3]}{MASK}{destination[-3:]}'


def _log(
    notification: Notification, result: str, error: Exception | None = None
) -> None:
    level = logging.INFO if error is None else logging.WARNING
    logger.log(
        level,
        DELIVERY_LOG,
        notification.notice_id,
        notification.channel,
        result,
        _masked(notification.channel, notification.destination),
        notification.subject,
        notification.body,
        error or '-',
    )
