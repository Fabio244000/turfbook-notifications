import json
from typing import Protocol

# CloudFormation rejects response bodies over 4096 bytes; the reason is the only
# field that can grow (e.g. a long validation error).
MAX_REASON_LENGTH = 1000
DEFAULT_REASON = 'See CloudWatch Logs for detail.'


class Migrator(Protocol):
    def upgrade(self) -> None: ...


class ResponseSender(Protocol):
    def send(self, url: str, body: bytes) -> None: ...


def handle_migration_event(
    event: dict[str, object], migrator: Migrator, sender: ResponseSender
) -> None:
    """CloudFormation Custom Resource provider: runs the migrations on Create and
    Update, and always reports the result so the stack never waits for a reply."""
    url = str(event['ResponseURL'])
    try:
        if event.get('RequestType') != 'Delete':
            migrator.upgrade()
    except Exception as error:
        reason = str(error) or DEFAULT_REASON
        sender.send(url, build_response_body(event, 'FAILED', reason))
        raise
    sender.send(url, build_response_body(event, 'SUCCESS', DEFAULT_REASON))


def build_response_body(event: dict[str, object], status: str, reason: str) -> bytes:
    return json.dumps(
        {
            'Status': status,
            'Reason': reason[:MAX_REASON_LENGTH],
            'PhysicalResourceId': event['LogicalResourceId'],
            'StackId': event['StackId'],
            'RequestId': event['RequestId'],
            'LogicalResourceId': event['LogicalResourceId'],
        }
    ).encode('utf-8')
