# 🛠️ Saturnus_Magister Setup Guide

Setup instructions for the development environment. Uses **`uv`** for dependency management to ensure speed, consistency, and isolation from system Python.

## Background

### 1. Virtual Environment Isolation
System Python (typically 3.12 on Linux/WSL2) is used by the operating system for internal tasks.
- **Risk**: Installing packages globally can break system tools or cause version conflicts between projects.
- **Solution**: Virtual environments provide per-project isolation.

### 2. Using `uv`
Modern, fast Python package installer and resolver.
- Manages Python versions locally without affecting system installation
- Creates virtual environments instantly
- Resolves dependencies faster than pip

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
Create a virtual environment using Python 3.14 for this project.

```bash
# Create .venv with Python 3.14
uv venv .venv --python 3.14
```

*Creates `.venv/` directory containing standalone Python installation.*

### 2. Activate Environment
Activate the virtual environment to use it instead of system Python.

```bash
source .venv/bin/activate
```

*Terminal prompt will show `(.venv)` when active.*

### 3. Install Dependencies
Install packages defined in `pyproject.toml`.

```bash
# Install in editable mode with dev dependencies
uv pip install -e ".[dev]"
```

### 4. Generate Lockfile (Optional)
Create `requirements.txt` for reproducible builds.

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
