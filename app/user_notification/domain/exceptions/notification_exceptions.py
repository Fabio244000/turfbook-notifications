from app.user_notification.domain.exceptions.domain_error import DomainError
from app.user_notification.domain.messages import NOTIFICATION_ALREADY_RESERVED


class NotificationAlreadyReservedError(DomainError):
    """Another delivery of the same notice reserved the channel first: retrying later
    finds that record and does not send twice."""

    def __init__(self) -> None:
        super().__init__(NOTIFICATION_ALREADY_RESERVED)
