from dataclasses import dataclass


@dataclass(frozen=True)
class OutgoingMessage:
    """What one channel delivers: the body as the user must read it (with a security
    code in place), which lives only in memory and is never recorded."""

    destination: str
    subject: str
    body: str
