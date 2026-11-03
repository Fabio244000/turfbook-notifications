from abc import ABC, abstractmethod
from typing import Self

from app.user_notification.domain.ports.output.notification_repository_port import (
    NotificationRepositoryPort,
)


class UnitOfWorkPort(ABC):
    notifications: NotificationRepositoryPort

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *args: object) -> None:
        """Leaving the block without commit() discards the work; after a commit
        there is nothing left to roll back."""
        await self.rollback()

    @abstractmethod
    async def commit(self) -> None: ...

    @abstractmethod
    async def rollback(self) -> None: ...
