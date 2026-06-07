from datetime import datetime, time, timezone
from types import SimpleNamespace

from core.models import AudioSpotInsertionPolicy
from services.audio_spot_scheduler import _schedule_matches_now
from services.schedule_clock import normalize_schedule_now
from services.spot_resolver import _resolve_insertion_policy


def test_schedule_clock_converts_aware_utc_to_app_timezone():
    utc_now = datetime(2026, 6, 6, 22, 56, tzinfo=timezone.utc)

    assert normalize_schedule_now(utc_now) == datetime(2026, 6, 6, 19, 56)


def test_audio_spot_scheduler_accepts_cross_midnight_window():
    schedule = SimpleNamespace(
        starts_at=None,
        ends_at=None,
        start_time="22:00",
        end_time="06:00",
    )

    assert _schedule_matches_now(schedule, datetime(2026, 6, 6).date(), time(23, 0))
    assert _schedule_matches_now(schedule, datetime(2026, 6, 7).date(), time(5, 59))
    assert not _schedule_matches_now(schedule, datetime(2026, 6, 7).date(), time(12, 0))


def test_spot_resolver_returns_enum_value_for_insertion_policy():
    schedule = SimpleNamespace(insertion_policy=AudioSpotInsertionPolicy.INTERRUPT)
    spot = SimpleNamespace(insertion_policy=AudioSpotInsertionPolicy.WAIT_SILENCE)

    assert _resolve_insertion_policy(schedule, spot) == "interrupt"
