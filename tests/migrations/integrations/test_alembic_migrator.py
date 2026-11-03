from pathlib import Path
from uuid import uuid4

import pytest
from alembic.util.exc import CommandError
from sqlalchemy.engine import make_url

from app.migrations.alembic_migrator import (
    DATABASE_NOT_READY_MESSAGE,
    AlembicMigrator,
    DatabaseNotReadyError,
)
from app.migrations.custom_resource import handle_migration_event
from app.migrations.handler import ALEMBIC_INIT_PATH
from config.settings import settings
from tests.fakes.migrations import FakeResponseSender


def _url_of_a_database_that_does_not_exist() -> str:
    missing = make_url(settings.database_url).set(database=f'missing_{uuid4().hex}')
    return missing.render_as_string(hide_password=False)


class TestAlembicMigrator:
    def test_running_migrations_twice_is_idempotent(self) -> None:
        event: dict[str, object] = {
            'RequestType': 'Update',
            'ResponseURL': 'https://cloudformation-custom-resource-response.s3.amazonaws.com/x',
            'StackId': 'arn:aws:cloudformation:us-east-1:123456789012:stack/test/abc',
            'RequestId': 'request-123',
            'LogicalResourceId': 'MigrationTrigger',
        }
        migrator, sender = AlembicMigrator(ALEMBIC_INIT_PATH), FakeResponseSender()

        handle_migration_event(event, migrator, sender)
        handle_migration_event(event, migrator, sender)

        assert [body['Status'] for _, body in sender.sent] == ['SUCCESS', 'SUCCESS']

    def test_reports_a_clear_error_when_the_database_is_not_provisioned(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Only the configuration changes: the real PostgreSQL answers that the
        # database does not exist.
        monkeypatch.setattr(
            settings, 'database_url', _url_of_a_database_that_does_not_exist()
        )

        with pytest.raises(DatabaseNotReadyError, match=DATABASE_NOT_READY_MESSAGE):
            AlembicMigrator(ALEMBIC_INIT_PATH).upgrade()

    def test_lets_any_other_error_pass_through(self, tmp_path: Path) -> None:
        ini_without_scripts = tmp_path / 'alembic.ini'
        ini_without_scripts.write_text('[alembic]\n')

        with pytest.raises(CommandError, match='script_location'):
            AlembicMigrator(ini_without_scripts).upgrade()
