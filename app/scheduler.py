from __future__ import annotations

from datetime import date, datetime, timedelta
from math import ceil
from zoneinfo import ZoneInfo

from app.models import BusyInterval, CandidateSlot, ScheduleRequest


def _ceil_to_interval(value: datetime, interval_minutes: int) -> datetime:
    """Round a datetime up to the next scheduling boundary."""

    midnight = value.replace(hour=0, minute=0, second=0, microsecond=0)
    elapsed_minutes = (value - midnight).total_seconds() / 60
    rounded_minutes = ceil(elapsed_minutes / interval_minutes) * interval_minutes
    return midnight + timedelta(minutes=rounded_minutes)


def _overlaps(start: datetime, end: datetime, busy: BusyInterval) -> bool:
    return start < busy.end and end > busy.start


def _score_slot(
    request: ScheduleRequest,
    start: datetime,
    end: datetime,
    busy_intervals: list[BusyInterval],
) -> tuple[float, list[str]]:
    score = 100.0
    reasons = ["all required attendees are available"]

    if request.preferred_start_hour is not None:
        start_hour = start.hour + start.minute / 60
        distance = abs(start_hour - request.preferred_start_hour)
        preference_bonus = max(0.0, 25.0 - (5.0 * distance))
        score += preference_bonus
        reasons.append(
            f"starts {distance:g} hour(s) from the preferred time"
            if distance
            else "starts at the preferred time"
        )

    touches_existing_event = any(
        start == interval.end or end == interval.start for interval in busy_intervals
    )
    if touches_existing_event:
        score -= 5.0
        reasons.append("includes a back-to-back meeting penalty")
    else:
        score += 3.0
        reasons.append("leaves a buffer around existing meetings")

    return score, reasons


def _iter_dates(first: date, last: date):
    current = first
    while current <= last:
        yield current
        current += timedelta(days=1)


def find_candidate_slots(
    request: ScheduleRequest,
    busy_intervals: list[BusyInterval],
) -> list[CandidateSlot]:
    """Return the highest-scoring feasible slots for a meeting request."""

    timezone = ZoneInfo(request.timezone)
    window_start = request.window_start.astimezone(timezone)
    window_end = request.window_end.astimezone(timezone)
    localized_busy = [
        BusyInterval(
            calendar_id=interval.calendar_id,
            start=interval.start.astimezone(timezone),
            end=interval.end.astimezone(timezone),
        )
        for interval in busy_intervals
    ]

    duration = timedelta(minutes=request.duration_minutes)
    step = timedelta(minutes=request.slot_interval_minutes)
    candidates: list[CandidateSlot] = []

    for day in _iter_dates(window_start.date(), window_end.date()):
        if day.weekday() >= 5:
            continue

        day_start = datetime.combine(day, request.workday_start, tzinfo=timezone)
        day_end = datetime.combine(day, request.workday_end, tzinfo=timezone)
        available_start = max(day_start, window_start)
        available_end = min(day_end, window_end)
        slot_start = _ceil_to_interval(available_start, request.slot_interval_minutes)

        while slot_start + duration <= available_end:
            slot_end = slot_start + duration
            if not any(_overlaps(slot_start, slot_end, interval) for interval in localized_busy):
                score, reasons = _score_slot(request, slot_start, slot_end, localized_busy)
                candidates.append(
                    CandidateSlot(
                        start=slot_start,
                        end=slot_end,
                        score=score,
                        reasons=reasons,
                    )
                )
            slot_start += step

    candidates.sort(key=lambda slot: (-slot.score, slot.start))
    return candidates[: request.top_k]
# temporary per-file commit marker
