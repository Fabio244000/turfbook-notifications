import json


class FakeMigrator:
    def __init__(self, error: Exception | None = None) -> None:
        self.calls = 0
        self._error = error

    def upgrade(self) -> None:
        self.calls += 1
        if self._error is not None:
            raise self._error


class FakeResponseSender:
    def __init__(self) -> None:
        self.sent: list[tuple[str, dict[str, str]]] = []

    def send(self, url: str, body: bytes) -> None:
        self.sent.append((url, json.loads(body)))

    @property
    def last_body(self) -> dict[str, str]:
        return self.sent[-1][1]
