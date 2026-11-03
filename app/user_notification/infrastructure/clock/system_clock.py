from datetime import UTC, datetime

from app.user_notification.domain.ports.output.clock_port import ClockPort


class SystemClock(ClockPort):
    def now(self) -> datetime:
        return datetime.now(UTC)
