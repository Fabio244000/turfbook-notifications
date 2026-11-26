from pathlib import Path

from app.migrations.alembic_migrator import AlembicMigrator
from app.migrations.custom_resource import handle_migration_event
from app.migrations.direct_actions import handle_direct_action, is_direct_action
from app.migrations.http_response_sender import HttpResponseSender

ALEMBIC_INI_PATH = Path(__file__).resolve().parents[2] / 'alembic.ini'
RESPONSE_TIMEOUT_SECONDS = 10


def handler(event: dict[str, object], context: object) -> dict[str, object]:
    """CloudFormation's Custom Resource event (migrations on deploy) or a direct
    action of the deploy (record the revision, undo the migrations)."""
    migrator = AlembicMigrator(ALEMBIC_INI_PATH)
    if is_direct_action(event):
        return dict(handle_direct_action(event, migrator))
    handle_migration_event(
        event,
        migrator=migrator,
        sender=HttpResponseSender(RESPONSE_TIMEOUT_SECONDS),
    )
    return {'status': 'ok'}
