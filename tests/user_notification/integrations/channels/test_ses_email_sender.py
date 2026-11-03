from collections.abc import Iterator
from typing import Any

import boto3
import pytest
from botocore.config import Config
from botocore.stub import Stubber

from app.user_notification.domain.exceptions import (
    DeliveryRejectedError,
    DeliveryUnavailableError,
)
from app.user_notification.infrastructure.channels.ses_email_sender import (
    SesEmailSender,
    build_ses_client,
)

SENDER = 'turfbook@gmail.com'
REGION = 'us-east-1'


def _client(**kwargs: Any) -> Any:
    """A real sesv2 client with fake credentials: nothing reaches AWS."""
    return boto3.client(
        'sesv2',
        region_name=REGION,
        aws_access_key_id='testing',
        aws_secret_access_key='testing',
        **kwargs,
    )


@pytest.fixture
def ses() -> Iterator[tuple[SesEmailSender, Stubber]]:
    """SES replaced by botocore's Stubber (a third party we cannot run locally)."""
    client = _client()
    with Stubber(client) as stubber:
        yield SesEmailSender(client=client, sender=SENDER), stubber
        stubber.assert_no_pending_responses()


class TestSesEmailSender:
    async def test_sends_the_notification_as_a_plain_text_email(
        self, ses, new_notification
    ):
        sender, stubber = ses
        notification = new_notification()
        stubber.add_response(
            'send_email',
            {'MessageId': 'message-1'},
            expected_params={
                'FromEmailAddress': SENDER,
                'Destination': {'ToAddresses': [notification.destination]},
                'Content': {
                    'Simple': {
                        'Subject': {'Data': notification.subject, 'Charset': 'UTF-8'},
                        'Body': {
                            'Text': {'Data': notification.body, 'Charset': 'UTF-8'}
                        },
                    }
                },
            },
        )

        await sender.send(notification)

    @pytest.mark.parametrize(
        'code',
        [
            'MessageRejected',
            'MailFromDomainNotVerifiedException',
            'BadRequestException',
            'NotFoundException',
        ],
    )
    async def test_a_rejection_of_the_email_is_permanent(
        self, ses, new_notification, code
    ):
        sender, stubber = ses
        stubber.add_client_error('send_email', service_error_code=code)

        with pytest.raises(DeliveryRejectedError, match=code):
            await sender.send(new_notification())

    @pytest.mark.parametrize(
        'code',
        [
            'TooManyRequestsException',
            'LimitExceededException',
            'SendingPausedException',
            'AccountSuspendedException',
        ],
    )
    async def test_throttling_or_a_paused_account_is_temporary(
        self, ses, new_notification, code
    ):
        sender, stubber = ses
        stubber.add_client_error('send_email', service_error_code=code)

        with pytest.raises(DeliveryUnavailableError, match=code):
            await sender.send(new_notification())

    async def test_an_unreachable_ses_is_temporary(self, new_notification):
        closed_port = 'http://127.0.0.1:9'
        client = _client(
            endpoint_url=closed_port,
            config=Config(connect_timeout=0.5, retries={'total_max_attempts': 1}),
        )
        sender = SesEmailSender(client=client, sender=SENDER)

        with pytest.raises(DeliveryUnavailableError):
            await sender.send(new_notification())


class TestBuildSesClient:
    def test_splits_the_limit_between_connecting_and_reading_without_retries(
        self,
    ):
        client = build_ses_client(region=REGION, timeout_seconds=1.0)

        config = client.meta.config
        assert (config.connect_timeout, config.read_timeout) == (0.5, 0.5)
        assert config.retries['total_max_attempts'] == 1
        assert client.meta.region_name == REGION
