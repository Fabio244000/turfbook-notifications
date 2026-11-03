from pathlib import Path

from app.migrations.alembic_migrator import AlembicMigrator
from app.migrations.custom_resource import handle_migration_event
from app.migrations.http_response_sender import HttpResponseSender

ALEMBIC_INIT_PATH = Path(__file__).resolve().parents[2] / 'alembic.ini'
RESPONSE_TIMEOUT_SECONDS = 10


def handler(event: dict[str, object], context: object) -> dict[str, str]:
    handle_migration_event(
        event,
        migrator=AlembicMigrator(ALEMBIC_INIT_PATH),
        sender=HttpResponseSender(RESPONSE_TIMEOUT_SECONDS),
    )
    return {'status': 'ok'}
