# 🛠️ Setup Guide

Welcome to the **Saturnus Magister** setup guide. This document will walk you through configuring your development environment step-by-step. We prioritize a clean, isolated setup to ensure stability and reproducibility.

---

## 1. Environment Management with `uv`

We use **`uv`** for project management. If you haven't used it before, you're in for a treat—it's an extremely fast replacement for `pip` and `virtualenv` written in Rust.

### Why Isolation Matters
System Python installations (like the one that comes with Ubuntu or macOS) are often cluttered or locked down. To avoid conflicts and ensure we're using the exact Python version we need (3.14+), we create a **virtual environment**. This is a self-contained directory that holds our specific Python executable and libraries.

### Installation Steps

1.  **Install `uv`** (if not already present):
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

2.  **Create the Virtual Environment**:
    This command creates a `.venv` folder in your project root. We explicitly request Python 3.14 to leverage its latest performance features.
    ```bash
    uv venv .venv --python 3.14
    ```

3.  **Activate the Environment**:
    This tells your shell to use the Python inside `.venv` instead of the global system Python.
    ```bash
    source .venv/bin/activate
    ```
    *You should see `(.venv)` appear in your terminal prompt.*

4.  **Install Dependencies**:
    We install the project in "editable" mode (`-e`), which means changes to the code are reflected immediately without reinstalling.
    ```bash
    uv pip install -e ".[dev]"
    ```

---

## 2. Database Configuration

Saturnus Magister relies on **PostgreSQL** for persistent storage. This allows us to maintain complex relationships between emails, tasks, and analytics over time.

Ensure you have a PostgreSQL instance running (locally or via Docker), then apply our schema migrations:

```bash
# Replace with your actual database URL
export DATABASE_URL=postgresql://user:password@localhost:5432/saturnus_db

# Initialize the core schema
psql $DATABASE_URL -f src/db/migrations/001_initial.sql

# Apply feature updates (e.g., countdown timers)
psql $DATABASE_URL -f src/db/migrations/002_add_countdown.sql
```

---

## 3. API Integrations

The power of Saturnus Magister comes from connecting your tools. You'll need to configure a few external services in your `.env` file.

### 🧠 AI Agent (LLM)
We support any OpenAI-compatible API. This gives you the flexibility to use:
-   **xAI (Grok)**: Excellent reasoning capabilities.
-   **OpenAI (GPT-4)**: Reliable standard.
-   **LocalAI / Ollama**: For privacy-focused, local inference.

Simply set `AGENT_BASE_URL` and `AGENT_API_KEY` accordingly.

### ✅ TickTick
To manage your tasks, we need OAuth access to your TickTick account.
1.  Register an app in the [TickTick Developer Portal](https://developer.ticktick.com/).
2.  Run our helper script to generate your access token:
    ```bash
    python scripts/ticktick_oauth.py
    ```
3.  Use the setup tool to map your projects (Eisenhower Matrix quadrants):
    ```bash
    saturnus-setup
    ```

### 📧 Gmail
We use the official Gmail API for reliable monitoring.
1.  Create a project in the [Google Cloud Console](https://console.cloud.google.com/).
2.  Enable the **Gmail API**.
3.  Download your `credentials.json` and place it in the project root.
4.  On first run, the application will open a browser window to authorize access.

---

## 4. Verification

Before letting it run wild on your inbox, it's good practice to verify everything is working.

**Run the Test Suite**:
```bash
pytest
```

**Run the Simulation**:
This runs a mock version of the pipeline to demonstrate the logic without touching real data.
```bash
PYTHONPATH=. python scripts/simulate_full_run.py
```

---

## 🎉 You're Ready!

Once configured, you can start the main processor:

```bash
python -m src.main
```

The system will now autonomously monitor your inbox, classify incoming messages, and organize your life in TickTick. Enjoy your newfound free time!
