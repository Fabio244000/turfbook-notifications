from datetime import timedelta

from app.user_notification.domain.entities.channel import Channel
from app.user_notification.domain.entities.notification import NotificationStatus
from app.user_notification.infrastructure.database.repositories.notification_repository import (
    NotificationRepository,
)


class TestNotificationRepository:
    async def test_gets_the_record_of_a_notice_and_channel(
        self, session, new_notification, insert_notification
    ):
        notification = new_notification()
        await insert_notification(notification)

        found = await NotificationRepository(session).get(
            notification.notice_id, Channel.EMAIL
        )

        assert found == notification

    async def test_another_channel_of_the_notice_has_no_record(
        self, session, new_notification, insert_notification
    ):
        notification = new_notification()
        await insert_notification(notification)

        found = await NotificationRepository(session).get(
            notification.notice_id, Channel.SMS
        )

        assert found is None

    async def test_add_saves_every_field(
        self, session, new_notification, stored_notification
    ):
        notification = new_notification(channel=Channel.SMS, destination='+51987654321')

        await NotificationRepository(session).add(notification)
        await session.flush()

        row = await stored_notification(notification.uuid)
        assert row == {
            'uuid': notification.uuid,
            'notice_id': notification.notice_id,
            'user_uuid': notification.user_uuid,
            'channel': 'sms',
            'destination': '+51987654321',
            'subject': notification.subject,
            'body': notification.body,
            'status': 'processing',
            'attempts': 1,
            'created_at': notification.created_at,
            'updated_at': notification.updated_at,
        }

    async def test_update_saves_the_new_state(
        self, session, new_notification, insert_notification, stored_notification
    ):
        notification = new_notification()
        await insert_notification(notification)
        later = notification.created_at + timedelta(minutes=1)
        notification.retry(later)
        notification.mark_sent(later)

        await NotificationRepository(session).update(notification)
        await session.flush()

        row = await stored_notification(notification.uuid)
        assert (row['status'], row['attempts'], row['updated_at']) == (
            NotificationStatus.SENT.value,
            2,
            later,
        )
