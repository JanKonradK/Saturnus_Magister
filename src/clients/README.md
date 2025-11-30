# `src/clients/` - External API Integrations

This module handles all communication with external services (Gmail, TickTick, Google Calendar).

## Components

### `gmail.py` - Gmail Client

Wrapper around the Google Gmail API (v1).

**Features**:
- **OAuth2 Authentication**: Handles token management and refreshing via `credentials.json` and `token.pickle`.
- **Message Retrieval**: Fetches emails from Inbox and Sent folders.
- **Parsing**: Extracts headers (Subject, From, To, Date) and decodes body content (Text/HTML).
- **State Management**: Supports querying for unread messages or messages after a specific date.

**Usage**:
```python
from src.clients.gmail import GmailClient

client = GmailClient()
client.authenticate()

# Get unread inbox messages
emails = await client.get_inbox_messages(only_unread=True)

# Get sent messages
sent = await client.get_sent_messages(max_results=20)
```

### `ticktick.py` - TickTick Client

Comprehensive client for the TickTick Open API (v1).

**Features**:
- **Task Creation**: Supports standard tasks with due dates, priorities, and tags.
- **Eisenhower Matrix**: Maps tasks to specific projects representing Q1-Q4 quadrants.
- **Calendar Events**: Creates tasks that sync to calendar views (start/end times).
- **Countdown Timers**: Enables countdown widgets for time-sensitive tasks.
- **Work Lists**: Manages a dedicated "Work" project for actionable items.

**Eisenhower Mapping**:
- **Q1 (Urgent + Important)**: `TICKTICK_Q1_PROJECT`
- **Q2 (Not Urgent + Important)**: `TICKTICK_Q2_PROJECT`
- **Q3 (Urgent + Not Important)**: `TICKTICK_Q3_PROJECT`
- **Q4 (Not Urgent + Not Important)**: `TICKTICK_Q4_PROJECT`

**Usage**:
```python
from src.clients.ticktick import TickTickClient, EisenhowerQuadrant, TaskPriority

client = TickTickClient()

# Create Eisenhower task
await client.create_eisenhower_task(
    title="Prepare for Interview",
    content="Review job description...",
    quadrant=EisenhowerQuadrant.Q1,
    priority=TaskPriority.HIGH
)

# Create Calendar event
await client.create_calendar_event(
    title="Interview: TechCorp",
    start_date=datetime(2025, 12, 15, 14, 0),
    content="Zoom link: ..."
)
```

### `gcal.py` - Google Calendar Client (Fallback)

Wrapper around Google Calendar API (v3).

**Note**: This is a **fallback client**. TickTick natively syncs tasks with start/end times to Google Calendar. We prefer using TickTick as the single source of truth. This client is provided for scenarios where direct GCal manipulation is required or TickTick sync is disabled.

**Features**:
- Event creation with reminders.
- Uses same OAuth credentials as Gmail client.

## Authentication

### Google (Gmail & Calendar)
- Requires `credentials.json` (OAuth 2.0 Client ID) from Google Cloud Console.
- Scopes: `gmail.readonly`, `gmail.send` (future), `calendar` (optional).
- First run opens browser for user consent; tokens saved to `token.pickle`.

### TickTick
- Requires OAuth 2.0 flow.
- Scopes: `tasks:write`, `tasks:read`.
- Setup script `scripts/ticktick_oauth.py` generates access token.
- Configuration via `.env` (`TICKTICK_ACCESS_TOKEN`, `TICKTICK_CLIENT_ID`, etc.).

## Error Handling

All clients implement robust error handling:
- `httpx` exceptions for HTTP errors.
- `googleapiclient.errors.HttpError` for Google API specific errors.
- Retries and graceful degradation (e.g., logging errors without crashing the main loop).
