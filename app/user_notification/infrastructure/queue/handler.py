import asyncio
import logging
from typing import Any

from app.user_notification.application.use_cases.send_notice import (
    SendNoticeUseCase,
)
from app.user_notification.domain.entities.channel import Channel
from app.user_notification.infrastructure.channels.ses_email_sender import (
    SesEmailSender,
    build_ses_client,
)
from app.user_notification.infrastructure.channels.simulated_sms_sender import (
    SimulatedSmsSender,
)
from app.user_notification.infrastructure.clock.system_clock import SystemClock
from app.user_notification.infrastructure.database.session import async_session
from app.user_notification.infrastructure.database.unit_of_work import (
    SqlAlchemyUnitOfWork,
)
from app.user_notification.infrastructure.queue.notice_consumer import (
    consume_notice,
)
from app.user_notification.infrastructure.queue.sqs_dead_letter_sender import (
    SqsDeadLetterSender,
    build_sqs_client,
)
from config.settings import settings

# The delivery log of each channel is INFO (CA8).
logging.getLogger().setLevel(logging.INFO)

# One event loop for the life of the execution environment (D2): the module-level
# engine keeps its connections on it across warm invocations.
_runner = asyncio.Runner()

_use_case = SendNoticeUseCase(
    uow=SqlAlchemyUnitOfWork(async_session),
    senders={
        Channel.EMAIL: SesEmailSender(
            client=build_ses_client(settings.ses_region, settings.ses_timeout_seconds),
            sender=settings.ses_sender,
        ),
        Channel.SMS: SimulatedSmsSender(),
    },
    clock=SystemClock(),
)
_dead_letters = SqsDeadLetterSender(
    client=build_sqs_client(settings.aws_region, settings.dlq_timeout_seconds),
    queue_url=settings.dlq_url,
)


def handler(event: dict[str, Any], context: object) -> None:
    """Lambda `notifier`: one SQS message per invocation (`batchSize: 1`)."""
    for record in event['Records']:
        _runner.run(consume_notice(record['body'], _use_case, _dead_letters))
