from typing import Self

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.user_notification.domain.ports.output.unit_of_work_port import UnitOfWorkPort
from app.user_notification.infrastructure.database.constraint_errors import (
    to_domain_error,
)
from app.user_notification.infrastructure.database.repositories.notification_repository import (
    NotificationRepository,
)


class SqlAlchemyUnitOfWork(UnitOfWorkPort):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def __aenter__(self) -> Self:
        self._session = self._session_factory()
        self.notifications = NotificationRepository(self._session)
        return await super().__aenter__()

    async def __aexit__(self, *args: object) -> None:
        await super().__aexit__(*args)
        await self._session.close()

    async def commit(self) -> None:
        try:
            await self._session.commit()
        except IntegrityError as error:
            domain_error = to_domain_error(error)
            if domain_error is None:
                raise  # no business meaning: a bug
            raise domain_error from error

    async def rollback(self) -> None:
        await self._session.rollback()
