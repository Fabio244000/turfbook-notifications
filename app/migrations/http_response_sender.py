import urllib.request


class HttpResponseSender:
    def __init__(self, timeout_seconds: float) -> None:
        self._timeout_seconds = timeout_seconds

    def send(self, url: str, body: bytes) -> None:
        request = urllib.request.Request(
            url=url, data=body, method='PUT', headers={'Content-type': ''}
        )
        with urllib.request.urlopen(request, timeout=self._timeout_seconds):
            pass
