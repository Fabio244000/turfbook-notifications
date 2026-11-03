import pytest

from app.migrations.custom_resource import (
    DEFAULT_REASON,
    MAX_REASON_LENGTH,
    handle_migration_event,
)
from tests.fakes.migrations import FakeMigrator, FakeResponseSender

RESPONSE_URL = 'https://cloudformation-custom-resource-response.s3.amazonaws.com/x'


def _build_event(request_type: str) -> dict[str, object]:
    return {
        'RequestType': request_type,
        'ResponseURL': RESPONSE_URL,
        'StackId': 'arn:aws:cloudformation:us-east-1:123456789012:stack/test/abc',
        'RequestId': 'request-123',
        'LogicalResourceId': 'MigrationTrigger',
    }


def _run_failing(error: Exception) -> FakeResponseSender:
    sender = FakeResponseSender()
    with pytest.raises(type(error)):
        handle_migration_event(_build_event('Create'), FakeMigrator(error), sender)
    return sender


class TestHandleMigrationEvent:
    @pytest.mark.parametrize('request_type', ['Create', 'Update'])
    def test_runs_migrations_and_reports_success(self, request_type: str) -> None:
        migrator, sender = FakeMigrator(), FakeResponseSender()

        handle_migration_event(_build_event(request_type), migrator, sender)

        assert migrator.calls == 1
        assert len(sender.sent) == 1
        assert sender.last_body['Status'] == 'SUCCESS'

    def test_skips_migrations_on_delete_and_reports_success(self) -> None:
        migrator, sender = FakeMigrator(), FakeResponseSender()

        handle_migration_event(_build_event('Delete'), migrator, sender)

        assert migrator.calls == 0
        assert sender.last_body['Status'] == 'SUCCESS'

    def test_reports_failure_and_reraises_when_migration_fails(self) -> None:
        sender = _run_failing(RuntimeError('boom'))

        assert len(sender.sent) == 1
        assert sender.last_body['Status'] == 'FAILED'
        assert sender.last_body['Reason'] == 'boom'

    def test_truncates_a_long_failure_reason(self) -> None:
        sender = _run_failing(RuntimeError('x' * 5000))

        assert len(sender.last_body['Reason']) == MAX_REASON_LENGTH

    def test_uses_default_reason_when_error_has_no_message(self) -> None:
        sender = _run_failing(RuntimeError())

        assert sender.last_body['Reason'] == DEFAULT_REASON

    def test_sends_the_cloudformation_identifiers_to_the_response_url(self) -> None:
        event, sender = _build_event('Create'), FakeResponseSender()

        handle_migration_event(event, FakeMigrator(), sender)

        url, body = sender.sent[0]
        assert url == RESPONSE_URL
        assert body['StackId'] == event['StackId']
        assert body['RequestId'] == event['RequestId']
        assert body['LogicalResourceId'] == 'MigrationTrigger'
        assert body['PhysicalResourceId'] == 'MigrationTrigger'
