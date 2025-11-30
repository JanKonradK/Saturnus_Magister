# 🛠️ Saturnus_Magister Setup Guide

This guide explains how to set up the development environment for Saturnus_Magister. We use **`uv`** for dependency management to ensure speed, consistency, and isolation from your system Python.

## 🧐 Why do we do this?

### 1. The "Global Python" Problem
Your operating system (Linux/WSL2) uses Python (likely version 3.12) for its own internal tasks.
- **Risk**: If you install libraries globally (e.g., `pip install pandas`), you might break system tools or cause version conflicts between projects.
- **Solution**: We **NEVER** install packages globally. We use **Virtual Environments**.

### 2. Why `uv`?
`uv` is a modern, extremely fast Python package installer and resolver.
- It manages Python versions for us (e.g., installing Python 3.14 locally without touching your system).
- It creates virtual environments instantly.
- It resolves dependencies faster than pip.

---

## 🚀 Step-by-Step Setup

### Prerequisites
The only global tool you need is `uv`.

```bash
# Check if installed
uv --version

# If not, install it:
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 1. Create Virtual Environment
We want to use Python 3.14 (or the latest supported version) specifically for this project.

```bash
# Create a virtual environment named '.venv' using Python 3.14
uv venv .venv --python 3.14
```

*This creates a folder `.venv/` containing a standalone Python installation just for this project.*

### 2. Activate the Environment
You need to tell your shell to use this environment instead of the global one.

```bash
source .venv/bin/activate
```

*You should see `(.venv)` appear in your terminal prompt.*

### 3. Install Dependencies
We install the libraries defined in `pyproject.toml`.

```bash
# Install project in editable mode (-e) with dev dependencies
uv pip install -e ".[dev]"
```

### 4. Generate Lockfile (Optional but Recommended)
To ensure everyone uses the *exact* same versions, we compile a `requirements.txt`.

```bash
uv pip compile pyproject.toml -o requirements.txt
```

---

## 🏃‍♂️ Running the Project

Always ensure your virtual environment is active (`source .venv/bin/activate`) before running commands.

```bash
# Run the main processor
python -m src.main

# Run the simulation
python scripts/simulate_full_run.py
```

## 🧹 Maintenance

To update dependencies:
1. Edit `pyproject.toml`
2. Run `uv pip install -e ".[dev]"`
3. Run `uv pip compile pyproject.toml -o requirements.txt`
