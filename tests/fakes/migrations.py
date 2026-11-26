import json


class FakeMigrator:
    def __init__(
        self, error: Exception | None = None, revision: str | None = None
    ) -> None:
        self.calls = 0
        self.downgraded_to: list[str] = []
        self.revision = revision
        self._error = error

    def upgrade(self) -> None:
        self.calls += 1
        if self._error is not None:
            raise self._error

    def current(self) -> str | None:
        return self.revision

    def downgrade(self, revision: str) -> str | None:
        self.downgraded_to.append(revision)
        self.revision = None if revision == 'base' else revision
        return self.revision


class FakeResponseSender:
    def __init__(self) -> None:
        self.sent: list[tuple[str, dict[str, str]]] = []

    def send(self, url: str, body: bytes) -> None:
        self.sent.append((url, json.loads(body)))

    @property
    def last_body(self) -> dict[str, str]:
        return self.sent[-1][1]
