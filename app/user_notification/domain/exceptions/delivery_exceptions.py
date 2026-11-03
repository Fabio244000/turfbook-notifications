from app.user_notification.domain.exceptions.domain_error import DomainError


class DeliveryRejectedError(DomainError):
    """The channel refused the notice for good (e.g. an invalid or unverified address):
    retrying cannot change it."""


class DeliveryUnavailableError(DomainError):
    """The channel could not take the notice now (no answer, throttling): a retry may
    succeed."""
