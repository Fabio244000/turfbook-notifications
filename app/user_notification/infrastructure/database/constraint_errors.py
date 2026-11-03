import psycopg
from sqlalchemy.exc import IntegrityError

from app.user_notification.domain.exceptions import (
    DomainError,
    NotificationAlreadyReservedError,
)

# Named unique constraints whose violation has a business meaning.
RESERVED_NOTIFICATION_CONSTRAINT = 'uq_notifications_notice_id_channel'


def to_domain_error(error: IntegrityError) -> DomainError | None:
    """The domain meaning of a violated constraint, or None when it has none."""
    if _constraint_name(error) == RESERVED_NOTIFICATION_CONSTRAINT:
        return NotificationAlreadyReservedError()
    return None


def _constraint_name(error: IntegrityError) -> str:
    if isinstance(error.orig, psycopg.Error):
        return error.orig.diag.constraint_name or ''
    return ''
