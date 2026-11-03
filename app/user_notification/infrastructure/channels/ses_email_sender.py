import asyncio
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.user_notification.domain.entities.notification import Notification
from app.user_notification.domain.exceptions import (
    DeliveryRejectedError,
    DeliveryUnavailableError,
)
from app.user_notification.domain.ports.output.channel_sender_port import (
    ChannelSenderPort,
)
from app.user_notification.infrastructure.channels.messages import (
    SES_ERROR,
    SES_UNREACHABLE,
)

# SES refuses this email for good: retrying cannot change it. Any other SES error
# (throttling, a paused or suspended account, an unknown code) is temporary.
PERMANENT_ERROR_CODES = frozenset(
    {
        'MessageRejected',
        'MailFromDomainNotVerifiedException',
        'BadRequestException',
        'NotFoundException',
    }
)
CHARSET = 'UTF-8'


def build_ses_client(region: str, timeout_seconds: float) -> Any:
    """An SES v2 client that gives up within `timeout_seconds`, with no retries:
    botocore has no total deadline, so connecting and reading get half each."""
    half = timeout_seconds / 2
    config = Config(
        connect_timeout=half,
        read_timeout=half,
        retries={'total_max_attempts': 1},
    )
    return boto3.client('sesv2', region_name=region, config=config)


class SesEmailSender(ChannelSenderPort):
    def __init__(self, client: Any, sender: str) -> None:
        self._client = client
        self._sender = sender

    async def send(self, notification: Notification) -> None:
        try:
            await asyncio.to_thread(self._send_email, notification)
        except ClientError as error:
            raise _delivery_error(error) from error
        except BotoCoreError as error:
            raise DeliveryUnavailableError(
                SES_UNREACHABLE.format(error=error)
            ) from error

    def _send_email(self, notification: Notification) -> None:
        self._client.send_email(
            FromEmailAddress=self._sender,
            Destination={'ToAddresses': [notification.destination]},
            Content={
                'Simple': {
                    'Subject': {'Data': notification.subject, 'Charset': CHARSET},
                    'Body': {'Text': {'Data': notification.body, 'Charset': CHARSET}},
                }
            },
        )


def _delivery_error(
    error: ClientError,
) -> DeliveryRejectedError | DeliveryUnavailableError:
    details = error.response.get('Error', {})
    code = details.get('Code', '')
    message = SES_ERROR.format(code=code, message=details.get('Message', ''))
    if code in PERMANENT_ERROR_CODES:
        return DeliveryRejectedError(message)
    return DeliveryUnavailableError(message)
