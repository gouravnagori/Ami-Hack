from abc import ABC, abstractmethod
from datetime import UTC, datetime


class Clock(ABC):
    """Abstract clock interface to allow deterministic time injection into business engines."""

    @abstractmethod
    def now(self) -> datetime:
        """Returns the current datetime, always timezone-aware in UTC."""
        pass


class SystemClock(Clock):
    """Production clock returning real-world system UTC time."""

    def now(self) -> datetime:
        return datetime.now(UTC)


class FrozenClock(Clock):
    """Deterministic clock for property testing, simulation, and scenario replay."""

    def __init__(self, current_time: datetime | None = None) -> None:
        if current_time is None:
            self._current_time = datetime.now(UTC)
        elif current_time.tzinfo is None:
            self._current_time = current_time.replace(tzinfo=UTC)
        else:
            self._current_time = current_time.astimezone(UTC)

    def now(self) -> datetime:
        return self._current_time

    def set_time(self, new_time: datetime) -> None:
        if new_time.tzinfo is None:
            self._current_time = new_time.replace(tzinfo=UTC)
        else:
            self._current_time = new_time.astimezone(UTC)

    def advance(self, **kwargs) -> datetime:
        """Advance time by timedelta kwargs (seconds=..., minutes=..., hours=...)."""
        from datetime import timedelta

        self._current_time += timedelta(**kwargs)
        return self._current_time


default_clock = SystemClock()


def get_clock() -> Clock:
    """FastAPI dependency to inject the current Clock."""
    return default_clock
