import pytest

from app.user_notification.domain.exceptions import NotificationAlreadyReservedError
from app.user_notification.infrastructure.database.unit_of_work import (
    SqlAlchemyUnitOfWork,
)


class TestSqlAlchemyUnitOfWork:
    async def test_commit_saves_the_work(
        self, session_factory, new_notification, stored_notification
    ):
        notification = new_notification()

        async with SqlAlchemyUnitOfWork(session_factory) as uow:
            await uow.notifications.add(notification)
            await uow.commit()

        assert await stored_notification(notification.uuid) is not None

    async def test_leaving_without_commit_discards_the_work(
        self, session_factory, new_notification, stored_notification
    ):
        notification = new_notification()

        async with SqlAlchemyUnitOfWork(session_factory) as uow:
            await uow.notifications.add(notification)
            await uow.notifications.get(  # sends the INSERT
                notification.notice_id, notification.channel
            )

        assert await stored_notification(notification.uuid) is None

    async def test_a_second_reservation_of_the_same_channel_is_a_domain_error(
        self, session_factory, new_notification, insert_notification
    ):
        reserved = new_notification()
        await insert_notification(reserved)
        concurrent = new_notification(notice_id=reserved.notice_id)

        with pytest.raises(NotificationAlreadyReservedError):
            async with SqlAlchemyUnitOfWork(session_factory) as uow:
                await uow.notifications.add(concurrent)
                await uow.commit()
