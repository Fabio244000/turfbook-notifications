from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncConnection

NOW = datetime(2026, 11, 2, 12, 0, tzinfo=UTC)

INSERT = text(
    'INSERT INTO notifications (uuid, notice_id, user_uuid, channel, destination,'
    ' subject, body, status, attempts, created_at, updated_at)'
    ' VALUES (:uuid, :notice_id, :user_uuid, :channel, :destination, :subject,'
    ' :body, :status, :attempts, :created_at, :updated_at)'
)


def _row(notice_id: UUID, channel: str) -> dict[str, Any]:
    return {
        'uuid': uuid4(),
        'notice_id': notice_id,
        'user_uuid': uuid4(),
        'channel': channel,
        'destination': 'luis.h@gmail.com' if channel == 'email' else '+51987654321',
        'subject': 'Tu cuenta de TurfBook fue bloqueada',
        'body': 'Hola Luis, tu cuenta de TurfBook fue bloqueada.',
        'status': 'processing',
        'attempts': 1,
        'created_at': NOW,
        'updated_at': NOW,
    }


class TestNotificationsTable:
    async def test_keeps_one_record_per_channel_of_a_notice(
        self, connection: AsyncConnection
    ) -> None:
        notice_id = uuid4()

        await connection.execute(INSERT, _row(notice_id, 'email'))
        await connection.execute(INSERT, _row(notice_id, 'sms'))

        count = await connection.scalar(
            text('SELECT count(*) FROM notifications WHERE notice_id = :id'),
            {'id': notice_id},
        )
        assert count == 2

    async def test_rejects_a_second_record_for_the_same_notice_and_channel(
        self, connection: AsyncConnection
    ) -> None:
        notice_id = uuid4()
        await connection.execute(INSERT, _row(notice_id, 'email'))

        with pytest.raises(IntegrityError, match='uq_notifications_notice_id_channel'):
            await connection.execute(INSERT, _row(notice_id, 'email'))
