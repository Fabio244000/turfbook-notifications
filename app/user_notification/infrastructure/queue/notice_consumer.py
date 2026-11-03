import logging
from typing import Protocol

from pydantic import ValidationError

from app.user_notification.domain.exceptions import InvalidNoticeError
from app.user_notification.domain.ports.input.send_notice_port import SendNoticePort
from app.user_notification.infrastructure.queue.messages import DEAD_LETTERED
from app.user_notification.infrastructure.queue.schemas import NoticeMessage

logger = logging.getLogger(__name__)


class DeadLetterSender(Protocol):
    async def send(self, body: str) -> None: ...


async def consume_notice(
    body: str, use_case: SendNoticePort, dead_letters: DeadLetterSender
) -> None:
    """Decides what the queue does with one message: returning deletes it, raising
    retries it, and a malformed notice goes to the DLQ at once (no retry can fix it).
    If the DLQ cannot be reached, raising falls back to the queue's retries."""
    try:
        message = NoticeMessage.model_validate_json(body)
        await use_case.execute(message.to_command())
    except ValidationError as error:
        await _dead_letter(body, dead_letters, _structure_errors(error))
    except InvalidNoticeError as error:
        await _dead_letter(body, dead_letters, str(error))


async def _dead_letter(body: str, dead_letters: DeadLetterSender, reason: str) -> None:
    await dead_letters.send(body)
    logger.warning(DEAD_LETTERED, reason)


def _structure_errors(error: ValidationError) -> str:
    """Where and what failed, never the received values (they hold contacts)."""
    return '; '.join(
        f'{".".join(str(part) for part in detail["loc"]) or "body"}: {detail["type"]}'
        for detail in error.errors(include_input=False)
    )
