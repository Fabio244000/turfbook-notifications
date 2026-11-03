import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession, async_sessionmaker

from app.user_notification.application.use_cases.send_notice import (
    SendNoticeUseCase,
)
from app.user_notification.domain.entities.channel import Channel
from app.user_notification.domain.exceptions import DeliveryUnavailableError
from app.user_notification.infrastructure.database.unit_of_work import (
    SqlAlchemyUnitOfWork,
)
from app.user_notification.infrastructure.queue.notice_consumer import (
    consume_notice,
)
from tests.fakes.user_notification import (
    FakeChannelSender,
    FakeClock,
    FakeDeadLetterSender,
)

NOW = datetime(2026, 11, 2, 12, 0, tzinfo=UTC)


def _notice(**overrides: Any) -> dict[str, Any]:
    """The contract's notice (§5), as SNS delivers it in the SQS body."""
    notice: dict[str, Any] = {
        'notice_id': str(uuid4()),
        'notifiers': ['email', 'sms'],
        'recipient': {
            'uuid': str(uuid4()),
            'email': 'luis.h@gmail.com',
            'cellphone': '+51987654321',
            'first_name': 'luis',
        },
        'subject': 'Tu cuenta de TurfBook fue bloqueada',
        'body': 'Hola Luis, tu cuenta de TurfBook fue bloqueada.',
    }
    notice.update(overrides)
    return notice


class _Queue:
    """The consumer over the real use case and database; channels and DLQ faked."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.email = FakeChannelSender()
        self.sms = FakeChannelSender()
        self.dead_letters = FakeDeadLetterSender()
        self.use_case = SendNoticeUseCase(
            uow=SqlAlchemyUnitOfWork(session_factory),
            senders={Channel.EMAIL: self.email, Channel.SMS: self.sms},
            clock=FakeClock(NOW),
        )

    async def deliver(self, body: str) -> None:
        await consume_notice(body, self.use_case, self.dead_letters)


@pytest.fixture
def queue(session_factory: async_sessionmaker[AsyncSession]) -> _Queue:
    return _Queue(session_factory)


async def _stored(connection: AsyncConnection, notice_id: str) -> dict[str, str]:
    """Each channel of the notice and its status, read with plain SQL."""
    result = await connection.execute(
        text('SELECT channel, status FROM notifications WHERE notice_id = :id'),
        {'id': UUID(notice_id)},
    )
    return {row.channel: row.status for row in result}


class TestNoticeConsumer:
    async def test_a_valid_notice_is_sent_and_recorded_per_channel(
        self, queue: _Queue, connection: AsyncConnection
    ) -> None:
        notice = _notice()

        await queue.deliver(json.dumps(notice))

        assert await _stored(connection, notice['notice_id']) == {
            'email': 'sent',
            'sms': 'sent',
        }
        assert queue.dead_letters.sent == []

    async def test_the_same_notice_delivered_twice_is_sent_once(
        self, queue: _Queue
    ) -> None:
        body = json.dumps(_notice())
        await queue.deliver(body)

        await queue.deliver(body)

        assert len(queue.email.sent) == len(queue.sms.sent) == 1

    @pytest.mark.parametrize(
        'body',
        [
            json.dumps({k: v for k, v in _notice().items() if k != 'notice_id'}),
            json.dumps(_notice(notifiers=['email', 'whatsapp'])),
            'not a json',
        ],
        ids=['without notice_id', 'unknown notifier', 'not json'],
    )
    async def test_a_malformed_message_goes_to_the_dlq_as_is_without_sending(
        self, queue: _Queue, body: str
    ) -> None:
        await queue.deliver(body)

        assert queue.dead_letters.sent == [body]
        assert queue.email.sent == queue.sms.sent == []

    async def test_a_notice_that_breaks_a_rule_goes_to_the_dlq_without_recording(
        self, queue: _Queue, connection: AsyncConnection
    ) -> None:
        notice = _notice(subject='   ')
        body = json.dumps(notice)

        await queue.deliver(body)

        assert queue.dead_letters.sent == [body]
        assert await _stored(connection, notice['notice_id']) == {}

    async def test_a_temporary_failure_is_raised_so_the_queue_retries(
        self, queue: _Queue
    ) -> None:
        queue.email.fail_with = DeliveryUnavailableError('timeout')

        with pytest.raises(DeliveryUnavailableError):
            await queue.deliver(json.dumps(_notice()))

        assert queue.dead_letters.sent == []

    async def test_when_the_dlq_cannot_be_reached_the_message_is_retried(
        self, queue: _Queue
    ) -> None:
        queue.dead_letters.fail_with = TimeoutError('no NAT')

        with pytest.raises(TimeoutError):
            await queue.deliver('not a json')
