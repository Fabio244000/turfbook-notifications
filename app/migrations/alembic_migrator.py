from pathlib import Path

from alembic.command import upgrade
from alembic.config import Config
from sqlalchemy.exc import OperationalError


class DatabaseNotReadyError(Exception):
    """The service database cannot be reached: not provisioned yet, wrong
    credentials in its secret, or the instance is unreachable."""


DATABASE_NOT_READY_MESSAGE = 'Database not provisioned or unreachable'


class AlembicMigrator:
    def __init__(self, ini_path: Path) -> None:
        self._init_path = ini_path

    def upgrade(self) -> None:
        try:
            upgrade(Config(str(self._init_path)), 'head')
        except OperationalError as error:
            raise DatabaseNotReadyError(
                f'{DATABASE_NOT_READY_MESSAGE}: {error.orig}'
            ) from error
