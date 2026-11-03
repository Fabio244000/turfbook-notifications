import asyncio
from typing import Any

import boto3
from botocore.config import Config


def build_sqs_client(region: str, timeout_seconds: float) -> Any:
    """An SQS client that gives up within `timeout_seconds`, with no retries:
    botocore has no total deadline, so connecting and reading get half each."""
    half = timeout_seconds / 2
    config = Config(
        connect_timeout=half,
        read_timeout=half,
        retries={'total_max_attempts': 1},
    )
    return boto3.client('sqs', region_name=region, config=config)


class SqsDeadLetterSender:
    """Sends a message body to the DLQ as is. Its errors are not translated: the
    consumer raises them, so the message falls back to the queue's retries."""

    def __init__(self, client: Any, queue_url: str) -> None:
        self._client = client
        self._queue_url = queue_url

    async def send(self, body: str) -> None:
        await asyncio.to_thread(
            self._client.send_message, QueueUrl=self._queue_url, MessageBody=body
        )
