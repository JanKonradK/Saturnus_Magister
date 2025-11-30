# `src/cli/` - Command Line Interface

This module provides interactive tools for managing the system and handling manual workflows.

## Tools

### `review.py` - Manual Review TUI

An interactive Terminal User Interface (TUI) for processing the Manual Review Queue.

**Command**: `saturnus-review`

**Features**:
- **Queue Display**: Shows pending reviews with reasons (e.g., "Low Confidence Match").
- **Email Inspection**: View subject, sender, body, and classification details.
- **Match Selection**: Presents ranked list of potential job matches from Nyx_Venatrix.
- **Actions**:
  - **Link**: Connect email to a specific job.
  - **No Match**: Mark email as unrelated to any job.
  - **Skip**: Defer decision.

**Built With**: `rich` library for beautiful terminal output.

### `setup.py` - TickTick Setup Helper

Utility to assist with the initial configuration of TickTick project IDs.

**Command**: `saturnus-setup`

**Purpose**:
1. Connects to TickTick API using your access token.
2. Fetches all projects.
3. Displays a table of Project Names and IDs.
4. Guides you on which IDs to copy to your `.env` file for Eisenhower Matrix configuration.

### `search.py` - Job Search (Phase 2)

*Placeholder for future functionality.*

**Planned Features**:
- Search for emails by content/sender.
- Manually link historical emails to jobs.
- Retroactive processing.

## Usage

All tools are installed as console scripts:

```bash
# Start the manual review interface
saturnus-review

# Run the setup helper
saturnus-setup
```

Alternatively, run via python module:

```bash
python -m src.cli.review
python -m src.cli.setup
```
