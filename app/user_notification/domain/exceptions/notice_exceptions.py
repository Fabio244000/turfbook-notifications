from app.user_notification.domain.exceptions.domain_error import DomainError


class InvalidNoticeError(DomainError):
    """A notice that breaks the rules of the contract (§4), with every failing field."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = tuple(errors)
        super().__init__(' '.join(errors))
