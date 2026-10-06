# Smart Scheduler

An agentic scheduling assistant that turns a natural-language meeting request into
validated constraints, checks calendar availability, and recommends high-quality
meeting times.

## Current milestone: deterministic scheduling core

The first milestone is intentionally local and credential-free. It provides:

- A FastAPI endpoint for structured scheduling requests
- Timezone-aware candidate generation
- Busy-time and weekend filtering
- Preference scoring and back-to-back meeting penalties
- Automated tests with fixed calendar scenarios

Natural-language extraction, Google Calendar, LangGraph, OR-Tools, and preference
learning are added in later milestones after this core is verified.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000/docs> to use the interactive API page.

## Try a scheduling request

From a second terminal:

```bash
curl -X POST http://127.0.0.1:8000/schedule/options \
  -H 'Content-Type: application/json' \
  -d '{
    "request": {
      "title": "Project sync",
      "attendees": ["alex@example.com", "sam@example.com"],
      "duration_minutes": 60,
      "window_start": "2026-10-12T09:00:00-05:00",
      "window_end": "2026-10-12T17:00:00-05:00",
      "timezone": "America/Chicago",
      "preferred_start_hour": 14,
      "top_k": 3
    },
    "busy_intervals": [
      {
        "calendar_id": "sam@example.com",
        "start": "2026-10-12T14:00:00-05:00",
        "end": "2026-10-12T15:00:00-05:00"
      }
    ]
  }'
```

## Test

```bash
pytest
```

## Project roadmap

- [x] Local API and deterministic scheduling core
- [ ] OR-Tools optimization and earliest-available baseline
- [ ] Natural-language extraction with structured model output
- [ ] LangGraph orchestration and confirmation state
- [ ] Google OAuth, free/busy lookup, and event creation
- [ ] Preference learning and synthetic evaluation suite
- [ ] Web interface, deployment, and calendar-change monitoring
