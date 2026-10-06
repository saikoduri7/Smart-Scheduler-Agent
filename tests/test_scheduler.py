from datetime import datetime
from zoneinfo import ZoneInfo

from app.models import BusyInterval, ScheduleRequest
from app.scheduler import find_candidate_slots

CENTRAL = ZoneInfo("America/Chicago")


def dt(day: int, hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 10, day, hour, minute, tzinfo=CENTRAL)


def test_prefers_requested_hour_and_skips_busy_time() -> None:
    request = ScheduleRequest(
        title="Project sync",
        attendees=["alex@example.com", "sam@example.com"],
        duration_minutes=60,
        window_start=dt(12, 9),
        window_end=dt(12, 17),
        preferred_start_hour=14,
        top_k=3,
    )
    busy = [
        BusyInterval(
            calendar_id="sam@example.com",
            start=dt(12, 14),
            end=dt(12, 15),
        )
    ]

    candidates = find_candidate_slots(request, busy)

    assert len(candidates) == 3
    assert candidates[0].start == dt(12, 12, 45)
    assert all(not (slot.start < dt(12, 15) and slot.end > dt(12, 14)) for slot in candidates)


def test_skips_weekends() -> None:
    request = ScheduleRequest(
        title="Planning session",
        duration_minutes=30,
        window_start=dt(10, 9),  # Saturday
        window_end=dt(12, 12),  # Monday
        top_k=5,
    )

    candidates = find_candidate_slots(request, [])

    assert candidates
    assert all(slot.start.weekday() < 5 for slot in candidates)
    assert candidates[0].start == dt(12, 9)


def test_penalizes_back_to_back_slots() -> None:
    request = ScheduleRequest(
        title="Design review",
        duration_minutes=30,
        window_start=dt(13, 9),
        window_end=dt(13, 12),
        preferred_start_hour=10,
        top_k=10,
    )
    busy = [
        BusyInterval(
            calendar_id="primary",
            start=dt(13, 10, 30),
            end=dt(13, 11),
        )
    ]

    candidates = find_candidate_slots(request, busy)
    by_start = {candidate.start: candidate for candidate in candidates}

    assert by_start[dt(13, 10)].score < by_start[dt(13, 9, 45)].score
