class DomainError(Exception):
    """Base of every business error; each entry point (API, queue) maps every subclass
    to its outcome."""
