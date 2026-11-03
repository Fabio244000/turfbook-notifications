from abc import ABC, abstractmethod
from uuid import UUID

from app.user_notification.domain.entities.channel import Channel
from app.user_notification.domain.entities.notification import Notification


class NotificationRepositoryPort(ABC):
    @abstractmethod
    async def get(self, notice_id: UUID, channel: Channel) -> Notification | None: ...

    @abstractmethod
    async def add(self, notification: Notification) -> None: ...

    @abstractmethod
    async def update(self, notification: Notification) -> None: ...
