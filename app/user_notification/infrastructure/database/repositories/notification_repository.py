from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.user_notification.domain.entities.channel import Channel
from app.user_notification.domain.entities.notification import (
    Notification,
    NotificationStatus,
)
from app.user_notification.domain.ports.output.notification_repository_port import (
    NotificationRepositoryPort,
)
from app.user_notification.infrastructure.database.models import NotificationModel


class NotificationRepository(NotificationRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, notice_id: UUID, channel: Channel) -> Notification | None:
        query = select(NotificationModel).where(
            NotificationModel.notice_id == notice_id,
            NotificationModel.channel == channel.value,
        )
        model = (await self._session.execute(query)).scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def add(self, notification: Notification) -> None:
        self._session.add(self._to_model(notification))

    async def update(self, notification: Notification) -> None:
        await self._session.merge(self._to_model(notification))

    def _to_model(self, notification: Notification) -> NotificationModel:
        return NotificationModel(
            uuid=notification.uuid,
            notice_id=notification.notice_id,
            user_uuid=notification.user_uuid,
            channel=notification.channel.value,
            destination=notification.destination,
            subject=notification.subject,
            body=notification.body,
            status=notification.status.value,
            attempts=notification.attempts,
            created_at=notification.created_at,
            updated_at=notification.updated_at,
        )

    def _to_entity(self, model: NotificationModel) -> Notification:
        return Notification(
            uuid=model.uuid,
            notice_id=model.notice_id,
            user_uuid=model.user_uuid,
            channel=Channel(model.channel),
            destination=model.destination,
            subject=model.subject,
            body=model.body,
            status=NotificationStatus(model.status),
            attempts=model.attempts,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
