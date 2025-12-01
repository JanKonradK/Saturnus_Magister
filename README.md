# Saturnus Magister 🪐

**Saturnus Magister** is an intelligent, autonomous email orchestration system designed to reclaim your time. It transforms your Gmail inbox into a structured, prioritized task list in TickTick, powered by advanced AI classification.

---

## ⚡️ Overview

Managing a high volume of emails—especially during job searches or busy project periods—can be overwhelming. Important deadlines get buried, and context switching destroys productivity.

**Saturnus Magister** solves this by acting as your personal executive assistant. It monitors your communications 24/7, understands the context of every email using Large Language Models (LLMs), and intelligently routes actionable items to your task management system.

It doesn't just "forward" emails; it **understands** them.

### Key Capabilities

-   🧠 **Cognitive Classification**: Uses state-of-the-art LLMs (via OpenAI-compatible APIs) to categorize emails with human-level nuance. It distinguishes between a generic update and an urgent interview invitation.
-   🎯 **Eisenhower Matrix Routing**: Automatically prioritizes tasks into Q1 (Urgent/Important) through Q4, ensuring you focus on what actually moves the needle.
-   📅 **Smart Scheduling**: Detects dates and deadlines in email bodies and syncs them directly to your calendar via TickTick.
-   🔍 **Contextual Matching**: Links incoming correspondence to your existing projects or job applications using fuzzy matching and AI disambiguation.
-   📊 **Insightful Analytics**: Tracks response rates, sentiment trends, and interaction history to give you a high-level view of your communications.

## 🛠️ Technology Stack

Built with modern, production-grade Python standards:

-   **Python 3.14+**: Leveraging the latest features, including free-threading support for high-performance parallel processing.
-   **PostgreSQL 16+**: Robust, relational data storage for complex relationship tracking.
-   **`uv`**: Blazing fast Python package and project management.
-   **Pydantic**: Strict data validation and settings management.
-   **Rich**: Beautiful, informative terminal output for CLI tools.

## 🚀 Getting Started

We've designed the setup process to be as smooth as possible. You can run Saturnus Magister directly on your machine or within a Docker container.

### Prerequisites

-   **Python 3.14+**
-   **PostgreSQL** database
-   **Gmail API** credentials (OAuth 2.0)
-   **TickTick** account (Premium recommended for full API access)
-   **LLM API Key** (OpenAI, Anthropic, xAI, or local equivalent)

### Quick Install

1.  **Clone and Setup**:
    ```bash
    # We recommend using 'uv' for a fast, isolated environment
    uv venv .venv --python 3.14
    source .venv/bin/activate
    uv pip install -e ".[dev]"
    ```

2.  **Database Initialization**:
    ```bash
    # Apply the schema to your PostgreSQL instance
    psql $DATABASE_URL -f src/db/migrations/001_initial.sql
    psql $DATABASE_URL -f src/db/migrations/002_add_countdown.sql
    ```

3.  **Configuration**:
    Copy `.env.example` to `.env` and populate your credentials.
    ```bash
    cp .env.example .env
    ```

    *Tip: Use the included helper script to easily find your TickTick project IDs:*
    ```bash
    saturnus-setup
    ```

4.  **Launch**:
    ```bash
    python -m src.main
    ```

For a detailed walkthrough, please refer to the [Setup Guide](SETUP_GUIDE.md).

## 🧪 Simulation Mode

Want to see it in action without configuring API keys? We've included a comprehensive simulation mode. This runs the entire processing pipeline using mocked services, allowing you to verify the logic and see how the system handles different email scenarios.

```bash
PYTHONPATH=. python scripts/simulate_full_run.py
```

## 📂 Project Structure

The codebase is organized for clarity and scalability:

-   `src/ai/`: Core intelligence. Contains the `EmailClassifier` and `JobMatcher` logic.
-   `src/services/`: Business logic layer. The `EmailProcessor` orchestrates the flow between components.
-   `src/clients/`: Robust API wrappers for Gmail, TickTick, and Google Calendar.
-   `src/db/`: Database models and asynchronous repository layer.
-   `src/cli/`: Terminal-based tools for setup and manual review.

## 🤝 Contributing

Contributions are welcome! Whether it's a bug fix, a new feature, or a documentation improvement, feel free to open a pull request. Please ensure you run the test suite before submitting:

```bash
pytest
```

## 📄 License

This project is licensed under the MIT License.
