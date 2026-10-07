from __future__ import annotations

from datetime import datetime, time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, Field, model_validator


class ScheduleRequest(BaseModel):
    """Structured constraints for one meeting request."""

    title: str = Field(min_length=1, max_length=200)
    attendees: list[str] = Field(default_factory=list)
    duration_minutes: int = Field(ge=15, le=480)
    window_start: datetime
    window_end: datetime
    timezone: str = "America/Chicago"
    workday_start: time = time(9, 0)
    workday_end: time = time(17, 0)
    preferred_start_hour: int | None = Field(default=None, ge=0, le=23)
    slot_interval_minutes: int = Field(default=15, ge=5, le=60)
    top_k: int = Field(default=3, ge=1, le=20)

    @model_validator(mode="after")
    def validate_constraints(self) -> ScheduleRequest:
        if self.window_start.tzinfo is None or self.window_end.tzinfo is None:
            raise ValueError("window_start and window_end must include a UTC offset")
        if self.window_end <= self.window_start:
            raise ValueError("window_end must be later than window_start")
        if self.workday_end <= self.workday_start:
            raise ValueError("workday_end must be later than workday_start")
        if self.duration_minutes % self.slot_interval_minutes != 0:
            raise ValueError("duration_minutes must be divisible by slot_interval_minutes")
        try:
            ZoneInfo(self.timezone)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(f"unknown timezone: {self.timezone}") from exc
        return self


class BusyInterval(BaseModel):
    """A period during which at least one required attendee is unavailable."""

    calendar_id: str
    start: datetime
    end: datetime

    @model_validator(mode="after")
    def validate_interval(self) -> BusyInterval:
        if self.start.tzinfo is None or self.end.tzinfo is None:
            raise ValueError("busy interval datetimes must include a UTC offset")
        if self.end <= self.start:
            raise ValueError("busy interval end must be later than its start")
        return self


class SchedulingInput(BaseModel):
    request: ScheduleRequest
    busy_intervals: list[BusyInterval] = Field(default_factory=list)


class CandidateSlot(BaseModel):
    start: datetime
    end: datetime
    score: float
    reasons: list[str]
