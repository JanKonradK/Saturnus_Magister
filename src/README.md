# `src/` - Core Application

This directory contains the main application code for Saturnus_Magister.

## Structure

```
src/
├── ai/              # AI classification and job matching
├── clients/         # External API integrations (Gmail, TickTick, GCal)
├── db/              # Database models, repository, migrations
├── services/        # Business logic and orchestration
├── cli/             # Command-line interface tools
├── config.py        # Pydantic settings and configuration
├── main.py          # Application entry point
└── __init__.py      # Package initialization
```

## Entry Point

**`main.py`** - Main application loop:
- Initializes all components (DB, Gmail, TickTick, AI)
- Runs processing loop every `POLL_INTERVAL_SECONDS` (default: 300s)
- Handles graceful shutdown (SIGINT/SIGTERM)
- Provides CLI entry point (`saturnus` command)

## Configuration

**`config.py`** - Centralized configuration using Pydantic Settings:
- Loads from `.env` file
- Validates all required settings
- Provides type-safe access to configuration
- Supports multiple environments (local, docker, aws, gcp)

```python
from src.config import settings

settings.database_url        # PostgreSQL connection string
settings.xai_api_key         # Grok API key
settings.ticktick_*          # TickTick OAuth tokens and project IDs
settings.auto_match_threshold # Job matching threshold (0.85)
```

## Module Organization

### AI (`ai/`)
AI-powered email classification and job matching logic.
See [`ai/README.md`](ai/README.md)

### Clients (`clients/`)
External API wrappers for Gmail, TickTick, and Google Calendar.
See [`clients/README.md`](clients/README.md)

### Database (`db/`)
PostgreSQL schema, Pydantic models, and async repository pattern.
See [`db/README.md`](db/README.md)

### Services (`services/`)
Business logic orchestration and workflow coordination.
See [`services/README.md`](services/README.md)

### CLI (`cli/`)
Command-line tools for manual review and setup.
See [`cli/README.md`](cli/README.md)

## Design Principles

1. **Separation of Concerns**: Each module has a single, well-defined responsibility
2. **Async/Await**: All I/O operations are asynchronous for performance
3. **Type Safety**: Pydantic models ensure type correctness throughout
4. **Error Handling**: Graceful degradation with comprehensive error logging
5. **Testability**: Dependency injection and modular design enable easy testing

## Data Flow

```
main.py
  ↓
EmailProcessor (services/)
  ↓
┌─────────────┬─────────────┬─────────────┐
│             │             │             │
GmailClient   Classifier    JobMatcher    TaskRouter
(clients/)    (ai/)         (ai/)         (services/)
  ↓             ↓             ↓             ↓
Gmail API    Grok API      Database      TickTick API
```

## Running the Application

```bash
# Direct
python -m src.main

# Installed
saturnus

# Docker
docker-compose up saturnus
```

## Development

```bash
# Type checking
mypy src

# Linting
ruff check src

# Tests
pytest
```
