from dataclasses import replace
from datetime import datetime
from uuid import UUID

from app.user_notification.domain.entities.channel import Channel
from app.user_notification.domain.entities.notification import Notification
from app.user_notification.domain.exceptions import DomainError
from app.user_notification.domain.ports.output.channel_sender_port import (
    ChannelSenderPort,
)
from app.user_notification.domain.ports.output.clock_port import ClockPort
from app.user_notification.domain.ports.output.notification_repository_port import (
    NotificationRepositoryPort,
)
from app.user_notification.domain.ports.output.unit_of_work_port import UnitOfWorkPort


class FakeNotificationRepository(NotificationRepositoryPort):
    """Like a database: it stores copies, and a write is kept only when the unit of
    work commits, so a test can tell what was committed before an error."""

    def __init__(self, notifications: list[Notification] | None = None) -> None:
        self.notifications = [replace(n) for n in notifications or []]
        self._pending: list[Notification] = []

    async def get(self, notice_id: UUID, channel: Channel) -> Notification | None:
        for notification in [*reversed(self._pending), *self.notifications]:
            if notification.notice_id == notice_id and notification.channel == channel:
                return replace(notification)
        return None

    async def add(self, notification: Notification) -> None:
        self._pending.append(replace(notification))

    async def update(self, notification: Notification) -> None:
        self._pending.append(replace(notification))

    def commit(self) -> None:
        for pending in self._pending:
            self.notifications = [
                n for n in self.notifications if n.uuid != pending.uuid
            ] + [pending]
        self._pending.clear()

    def rollback(self) -> None:
        self._pending.clear()

    def stored(self, notice_id: UUID, channel: Channel) -> Notification:
        return next(
            n
            for n in self.notifications
            if n.notice_id == notice_id and n.channel == channel
        )


class FakeUnitOfWork(UnitOfWorkPort):
    notifications: FakeNotificationRepository

    def __init__(self, notifications: list[Notification] | None = None) -> None:
        self.notifications = FakeNotificationRepository(notifications)

    async def commit(self) -> None:
        self.notifications.commit()

    async def rollback(self) -> None:
        self.notifications.rollback()


class FakeChannelSender(ChannelSenderPort):
    """Records what it sends; `fail_with` makes the next sends raise that error."""

    def __init__(self) -> None:
        self.sent: list[Notification] = []
        self.fail_with: DomainError | None = None

    async def send(self, notification: Notification) -> None:
        if self.fail_with is not None:
            raise self.fail_with
        self.sent.append(replace(notification))


class FakeClock(ClockPort):
    def __init__(self, now: datetime) -> None:
        self.current = now

    def now(self) -> datetime:
        return self.current


class FakeDeadLetterSender:
    """The DLQ in memory; `fail_with` makes the next sends raise that error."""

    def __init__(self) -> None:
        self.sent: list[str] = []
        self.fail_with: Exception | None = None

    async def send(self, body: str) -> None:
        if self.fail_with is not None:
            raise self.fail_with
        self.sent.append(body)
