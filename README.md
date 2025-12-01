# Saturnus Magister

**Saturnus Magister** is an intelligent, autonomous email orchestration system designed to reclaim your time. It transforms your Gmail inbox into a structured, prioritized task list in TickTick, powered by advanced AI classification.

---

## Overview

Managing a high volume of emails—especially during busy periods—can be overwhelming. **Saturnus Magister** acts as your personal executive assistant. It monitors your communications 24/7, understands the context of every email using Large Language Models (LLMs), and intelligently routes actionable items to your task management system.

### Key Capabilities

-    **Cognitive Classification**: Uses state-of-the-art LLMs to categorize emails with human-level nuance.
-    **Eisenhower Matrix Routing**: Prioritizes tasks into Q1 (Urgent/Important) through Q4.
-    **Smart Scheduling**: Detects dates/deadlines and syncs them to your calendar.
-    **Auto-Reply Agent**: Generates context-aware draft replies for common scenarios (e.g., interview confirmations).
-    **Analytics**: Tracks response rates and interaction history.

---

## Setup Guide

We use **`uv`** for fast, isolated environment management.

### 1. Prerequisites

-   **Python 3.14+** (Free-threading supported)
-   **PostgreSQL** database
-   **Gmail API Credentials** (`credentials.json`)
-   **TickTick Account**
-   **LLM API Key** (OpenAI, xAI, Anthropic, etc.)

### 2. Installation

```bash
# 1. Install uv (if needed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Create Virtual Environment (Python 3.14)
uv venv .venv --python 3.14
source .venv/bin/activate

# 3. Install Dependencies
uv pip install -e ".[dev]"
```

### 3. Configuration

1.  **Database**: Ensure PostgreSQL is running.
    ```bash
    # Initialize Schema
    psql $DATABASE_URL -f src/db/migrations/001_initial.sql
    psql $DATABASE_URL -f src/db/migrations/002_add_countdown.sql
    ```

2.  **Environment Variables**:
    Copy `.env.example` to `.env` and fill in your keys.
    ```bash
    cp .env.example .env
    ```

3.  **Gmail Auth**:
    Download your OAuth 2.0 Client ID JSON from Google Cloud Console, rename it to `credentials.json`, and place it in the project root.

4.  **TickTick Auth**:
    Run the helper to get your token and project IDs:
    ```bash
    python scripts/ticktick_oauth.py
    saturnus-setup
    ```

---

## Project Structure & Files

-   **`src/`**: Source code.
    -   `ai/`: LLM logic for classification and reply generation.
    -   `clients/`: API wrappers (Gmail, TickTick).
    -   `services/`: Core business logic (Processor, Router).
-   **`pyproject.toml`**: Python project configuration and dependencies.
-   **`requirements.txt`**: Lockfile ensuring reproducible builds (generated from pyproject.toml).
-   **`Makefile`**: Shortcut commands for common tasks (e.g., `make run`, `make test`).
-   **`credentials.json`**: (User provided) Google OAuth secrets. **Do not commit this.**
-   **`token.pickle`**: (Generated) Saved Gmail session token.

---

## Usage

### Run the System
```bash
python -m src.main
```

### Simulation Mode
Test the pipeline with mock data (no API keys needed):
```bash
PYTHONPATH=. python scripts/simulate_full_run.py
```

### Manual Review
Interactive terminal UI for ambiguous cases:
```bash
saturnus-review
```

---

## Auto-Reply Feature

The system can draft replies for specific categories (e.g., `interview_invite`, `follow_up_needed`).

-   **Draft Mode** (Default): Creates a draft in Gmail for you to review.
-   **Auto-Send**: Can be enabled in `.env` (use with caution!).

---

## Contributing

Contributions welcome! Please run tests before submitting:
```bash
pytest
```

## License

MIT License
