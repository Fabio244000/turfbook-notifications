import boto3
from botocore.stub import Stubber

from app.user_notification.infrastructure.queue.sqs_dead_letter_sender import (
    SqsDeadLetterSender,
    build_sqs_client,
)

REGION = 'us-east-1'
DLQ_URL = 'https://sqs.us-east-1.amazonaws.com/123456789012/turfbook-notifications-dev-notices-dlq'


class TestSqsDeadLetterSender:
    async def test_sends_the_body_to_the_dlq_unchanged(self) -> None:
        client = boto3.client(
            'sqs',
            region_name=REGION,
            aws_access_key_id='testing',
            aws_secret_access_key='testing',
        )
        body = '{"notifiers": ["whatsapp"]}'
        with Stubber(client) as stubber:
            stubber.add_response(
                'send_message',
                {'MessageId': 'message-1'},
                expected_params={'QueueUrl': DLQ_URL, 'MessageBody': body},
            )

            await SqsDeadLetterSender(client=client, queue_url=DLQ_URL).send(body)

            stubber.assert_no_pending_responses()


class TestBuildSqsClient:
    def test_splits_the_limit_between_connecting_and_reading_without_retries(
        self,
    ) -> None:
        client = build_sqs_client(region=REGION, timeout_seconds=1.0)

        config = client.meta.config
        assert (config.connect_timeout, config.read_timeout) == (0.5, 0.5)
        assert config.retries['total_max_attempts'] == 1
