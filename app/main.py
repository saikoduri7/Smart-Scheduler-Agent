from fastapi import FastAPI

from app.models import CandidateSlot, SchedulingInput
from app.scheduler import find_candidate_slots

app = FastAPI(
    title="Smart Scheduler",
    description="Generate ranked meeting times from structured constraints and availability.",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/schedule/options", response_model=list[CandidateSlot])
def schedule_options(payload: SchedulingInput) -> list[CandidateSlot]:
    return find_candidate_slots(payload.request, payload.busy_intervals)
