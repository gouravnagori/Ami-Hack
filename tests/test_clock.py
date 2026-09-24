from datetime import UTC, datetime

from app.core.clock import FrozenClock, SystemClock


def test_system_clock():
    clock = SystemClock()
    t = clock.now()
    assert t.tzinfo is not None
    assert t.tzinfo == UTC


def test_frozen_clock_advance():
    init_time = datetime(2026, 10, 1, 12, 0, 0, tzinfo=UTC)
    clock = FrozenClock(init_time)
    assert clock.now() == init_time

    # Advance 30 minutes
    advanced = clock.advance(minutes=30)
    assert advanced == datetime(2026, 10, 1, 12, 30, 0, tzinfo=UTC)
    assert clock.now() == advanced


def test_frozen_clock_set_time():
    clock = FrozenClock()
    target_time = datetime(2026, 12, 31, 23, 59, 59, tzinfo=UTC)
    clock.set_time(target_time)
    assert clock.now() == target_time
