# Setup Guide

Development environment setup using `uv` for dependency management.

## Tech Stack

- **Python**: 3.14+ (free-threading enabled)
- **Database**: PostgreSQL 16+
- **Package Manager**: `uv`
- **Dependencies**: See `pyproject.toml`

## Installation

### 1. Install `uv`

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Create Virtual Environment

```bash
uv venv .venv --python 3.14
```

### 3. Activate Environment

```bash
source .venv/bin/activate
```

### 4. Install Dependencies

```bash
uv pip install -e ".[dev]"
```

### 5. Generate Requirements Lockfile

```bash
uv pip compile pyproject.toml -o requirements.txt
```

## Database Setup

```bash
# Run migrations
psql $DATABASE_URL -f src/db/migrations/001_initial.sql
psql $DATABASE_URL -f src/db/migrations/002_add_countdown.sql
```

## Running

```bash
# Production
python -m src.main

# Simulation (no credentials required)
PYTHONPATH=. python scripts/simulate_full_run.py

# Tests
pytest
```

## Dependency Updates

```bash
# Edit pyproject.toml, then:
uv pip install -e ".[dev]"
uv pip compile pyproject.toml -o requirements.txt
```
