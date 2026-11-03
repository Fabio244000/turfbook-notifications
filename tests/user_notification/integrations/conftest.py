from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.user_notification.domain.entities.channel import Channel
from app.user_notification.domain.entities.notification import Notification

RESERVED_AT = datetime(2026, 11, 2, 12, 0, tzinfo=UTC)


@pytest.fixture
def new_notification() -> Callable[..., Notification]:
    """Builds a valid email notification of a notice no other row uses."""

    def _new_notification(**overrides: Any) -> Notification:
        data: dict[str, Any] = {
            'notice_id': uuid4(),
            'user_uuid': uuid4(),
            'channel': Channel.EMAIL,
            'destination': 'luis.h@gmail.com',
            'subject': 'Tu cuenta de TurfBook fue bloqueada',
            'body': 'Hola Luis, tu cuenta de TurfBook fue bloqueada.',
            'created_at': RESERVED_AT,
            'updated_at': RESERVED_AT,
        }
        data.update(overrides)
        return Notification(**data)

    return _new_notification


@pytest.fixture
def insert_notification(
    connection: AsyncConnection,
) -> Callable[[Notification], Awaitable[None]]:
    async def _insert_notification(notification: Notification) -> None:
        await connection.execute(
            text(
                'INSERT INTO notifications (uuid, notice_id, user_uuid, channel,'
                ' destination, subject, body, status, attempts, created_at,'
                ' updated_at) VALUES (:uuid, :notice_id, :user_uuid, :channel,'
                ' :destination, :subject, :body, :status, :attempts, :created_at,'
                ' :updated_at)'
            ),
            {
                'uuid': notification.uuid,
                'notice_id': notification.notice_id,
                'user_uuid': notification.user_uuid,
                'channel': notification.channel.value,
                'destination': notification.destination,
                'subject': notification.subject,
                'body': notification.body,
                'status': notification.status.value,
                'attempts': notification.attempts,
                'created_at': notification.created_at,
                'updated_at': notification.updated_at,
            },
        )

    return _insert_notification


@pytest.fixture
def stored_notification(
    connection: AsyncConnection,
) -> Callable[[UUID], Awaitable[dict[str, Any] | None]]:
    """The row as PostgreSQL has it, read with plain SQL."""

    async def _stored_notification(uuid: UUID) -> dict[str, Any] | None:
        result = await connection.execute(
            text('SELECT * FROM notifications WHERE uuid = :uuid'), {'uuid': uuid}
        )
        row = result.mappings().one_or_none()
        return dict(row) if row else None

    return _stored_notification
