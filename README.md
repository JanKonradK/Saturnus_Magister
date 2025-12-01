# Saturnus_Magister

Automated email processing system with AI classification, task management, and Eisenhower Matrix routing.

## Tech Stack

- Python 3.14+ (free-threading)
- PostgreSQL 16+
- Gmail API
- TickTick API
- OpenAI-compatible AI agent (xAI, OpenAI, Anthropic, etc.)

## Features

- Continuous Gmail monitoring (inbox + sent)
- AI-powered email classification and data extraction
- Eisenhower Matrix task routing (Q1-Q4)
- TickTick task creation with priorities, tags, due dates
- Google Calendar sync via TickTick
- Email analytics and manual review queue

## Installation

```bash
# Setup environment
uv venv .venv --python 3.14
source .venv/bin/activate
uv pip install -e ".[dev]"

# Run database migrations
psql $DATABASE_URL -f src/db/migrations/001_initial.sql
psql $DATABASE_URL -f src/db/migrations/002_add_countdown.sql
```

## Configuration

Create `.env`:
```env
DATABASE_URL=postgresql://user:password@host:5432/database

AGENT_API_KEY=your-key-here
AGENT_BASE_URL=https://api.x.ai/v1
AGENT_MODEL=grok-4-1-fast-reasoning

TICKTICK_ACCESS_TOKEN=...
TICKTICK_CLIENT_ID=...
TICKTICK_CLIENT_SECRET=...
TICKTICK_Q1_PROJECT=...
TICKTICK_Q2_PROJECT=...
TICKTICK_Q3_PROJECT=...
TICKTICK_Q4_PROJECT=...
TICKTICK_WORK_PROJECT=...
```

Get TickTick credentials: `python scripts/ticktick_oauth.py`
Get project IDs: `saturnus-setup`

## Usage

```bash
# Production
python -m src.main

# Simulation (no credentials)
PYTHONPATH=. python scripts/simulate_full_run.py

# Manual review queue
saturnus-review

# Docker
docker-compose -f docker/docker-compose.yml up -d
```

## Email Categories

**Inbound**: `interview_invite`, `assignment`, `rejection`, `offer`, `info`, `follow_up_needed`, `unknown`
**Outbound**: `sent_application`, `sent_availability`, `sent_follow_up`, `sent_documents`, `info`

Each email receives sentiment analysis (`positive`, `negative`, `neutral`) and data extraction (dates, deadlines, contacts).

## Eisenhower Routing

| Quadrant | Priority | Examples |
|----------|----------|----------|
| Q1 (Urgent + Important) | High | Time-sensitive deadlines |
| Q2 (Not Urgent + Important) | Medium-High | Important work, planning |
| Q3 (Urgent + Not Important) | Medium-Low | Quick acknowledgments |
| Q4 (Not Urgent + Not Important) | Low | Informational only |

## Architecture

```
src/
├── ai/              # Classification, matching
├── clients/         # Gmail, TickTick, GCal APIs
├── db/              # Models, repository, migrations
├── services/        # Email processor, task router
├── cli/             # Review queue, setup tools
└── main.py          # Entry point
```

## Development

```bash
pytest              # Tests
mypy src            # Type checking
ruff check src      # Linting
```

## Documentation

- [`SETUP_GUIDE.md`](SETUP_GUIDE.md) - Development environment
- [`SIMULATION.md`](SIMULATION.md) - Testing without credentials
- Folder-specific READMEs in `src/` subdirectories

## License

MIT
