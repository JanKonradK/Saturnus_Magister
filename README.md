# Saturnus_Magister

Automated email processing and task management system. Monitors Gmail, classifies emails using AI, and creates structured tasks in TickTick with Eisenhower Matrix prioritization.

## Features

- **Email Monitoring**: Continuous Gmail inbox and sent folder monitoring
- **AI Classification**: Automatic email categorization using OpenAI-compatible API
- **Task Automation**: Creates TickTick tasks with priority, tags, and due dates
- **Calendar Integration**: Syncs time-sensitive items to Google Calendar via TickTick
- **Eisenhower Matrix**: Automatic routing to Q1-Q4 quadrants based on urgency/importance
- **Analytics**: Tracks all processed emails for insights

## Architecture

```
saturnus_magister/
├── src/
│   ├── ai/              # Classification and matching logic
│   ├── clients/         # Gmail, TickTick, Google Calendar APIs
│   ├── db/              # PostgreSQL models, repository, migrations
│   ├── services/        # Email processor, task router
│   ├── cli/             # Manual review and setup tools
│   └── main.py          # Entry point
├── tests/               # Unit tests
├── scripts/             # Setup and simulation scripts
└── docker/              # Containerization
```

## Quick Start

### Prerequisites

- Python 3.14+ (3.13 acceptable)
- PostgreSQL
- Gmail API access
- TickTick account
- OpenAI-compatible API endpoint

### Installation

```bash
# Setup virtual environment
uv venv .venv --python 3.14
source .venv/bin/activate

# Install dependencies
uv pip install -e ".[dev]"

# Run migrations
psql $DATABASE_URL -f src/db/migrations/001_initial.sql
psql $DATABASE_URL -f src/db/migrations/002_add_countdown.sql
```

### Configuration

Create `.env`:
```env
DATABASE_URL=postgresql://user:password@host:5432/database
OPENAI_API_KEY=your-key-here
OPENAI_BASE_URL=https://api.openai.com/v1  # Or compatible endpoint
OPENAI_MODEL=gpt-4-turbo

TICKTICK_ACCESS_TOKEN=...
TICKTICK_CLIENT_ID=...
TICKTICK_CLIENT_SECRET=...
TICKTICK_Q1_PROJECT=...  # Urgent + Important
TICKTICK_Q2_PROJECT=...  # Not Urgent + Important
TICKTICK_Q3_PROJECT=...  # Urgent + Not Important
TICKTICK_Q4_PROJECT=...  # Not Urgent + Not Important
TICKTICK_WORK_PROJECT=...
```

### Run

```bash
# Production
python -m src.main

# Simulation (no API keys needed)
PYTHONPATH=. python scripts/simulate_full_run.py

# Docker
docker-compose -f docker/docker-compose.yml up -d
```

## Email Categories

System classifies emails into 14 categories:
- `interview_invite`, `assignment`, `rejection`, `offer`
- `info`, `follow_up_needed`, `unknown`
- `sent_application`, `sent_availability`, `sent_follow_up`, `sent_documents`

Each receives automatic sentiment analysis and data extraction (dates, deadlines, etc.).

## Eisenhower Matrix Routing

| Quadrant | Criteria | Example |
|----------|----------|---------|
| Q1 (Urgent + Important) | Time-sensitive, high priority | Interview invitations, urgent deadlines |
| Q2 (Not Urgent + Important) | Important but schedulable | Assignments, long-term planning |
| Q3 (Urgent + Not Important) | Quick actions required | Acknowledgments, minor updates |
| Q4 (Not Urgent + Not Important) | Low value | Informational only |

## CLI Tools

```bash
saturnus              # Main processor
saturnus-review       # Manual review queue
saturnus-setup        # TickTick project ID helper
```

## Development

```bash
# Tests
pytest

# Type checking
mypy src

# Linting
ruff check src
```

## Documentation

- [`SETUP_GUIDE.md`](SETUP_GUIDE.md) - Environment setup
- [`SIMULATION.md`](SIMULATION.md) - Running simulation mode
- Folder-specific READMEs in each `src/` subdirectory

## License

MIT
