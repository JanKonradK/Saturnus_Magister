# `src/db/` - Database Layer

This module manages data persistence, schema definitions, and database interactions.

## Architecture

Saturnus_Magister uses **PostgreSQL** as its primary data store. It is designed to share a database with [Nyx_Venatrix](https://github.com/JanKonradK/Nyx_Venatrix) to enable seamless linking between emails and job applications.

**Stack**:
- **Database**: PostgreSQL 16+
- **Driver**: `asyncpg` (High-performance async driver)
- **Models**: `Pydantic` (Data validation and type safety)
- **Migrations**: Raw SQL files (Simple, explicit schema management)

## Components

### `models.py` - Data Models

Pydantic models representing database entities. These ensure type safety throughout the application.

- **`EmailModel`**: Represents a stored email.
- **`EmailJobMatchModel`**: Link between an email and a job application.
- **`TickTickTaskModel`**: Tracks tasks created in TickTick.
- **`ManualReviewQueueModel`**: Items requiring human intervention.
- **`ResponseAnalyticsModel`**: Analytics data for email responses.
- **`CompanyBlocklistModel`**: Rules for auto-rejecting/blocking companies.

### `repository.py` - Database Repository

Implements the Repository pattern to abstract raw SQL queries.

**Key Methods**:
- `create_email()`, `get_email_by_gmail_id()`
- `create_match()`, `get_matches_for_email()`
- `create_task()`, `mark_task_synced()`
- `add_to_review_queue()`, `resolve_review()`
- `record_response()`, `get_success_rate_by_company()`

**Nyx_Venatrix Integration**:
- `get_recent_job_applications()`: Queries the shared `applied_jobs` table.

### `migrations/` - Schema Management

SQL scripts to initialize and update the database schema.

- **`001_initial.sql`**: Sets up core tables (`emails`, `matches`, `analytics`, etc.), indexes, and triggers.
- **`002_add_countdown.sql`**: Adds fields for TickTick countdown and calendar support.

## Schema Overview

```sql
-- Core Tables
emails (id, gmail_id, subject, body, category, sentiment...)
email_job_matches (email_id, job_id, score, match_method...)

-- Integration Tables
ticktick_tasks (email_id, ticktick_id, project_id, status...)
applied_jobs (SHARED with Nyx_Venatrix)

-- Workflow Tables
manual_review_queue (email_id, reason, status, resolution...)
company_blocklist (company_name, domain, reason...)
response_analytics (email_id, response_type, timeline_metrics...)
```

## Usage

```python
from src.db.repository import DatabaseRepository
from src.config import settings

db = DatabaseRepository(settings.database_url)
await db.initialize()

# Create an email
email = await db.create_email(email_model)

# Find matches
matches = await db.get_matches_for_email(email.id)

await db.close()
```

## Integration with Nyx_Venatrix

The system assumes the existence of an `applied_jobs` table in the same database (or accessible schema). This table is the source of truth for job applications.

**Expected `applied_jobs` Schema**:
- `id` (UUID)
- `company_name` (Text)
- `position_title` (Text)
- `applied_at` (Timestamp)
- `company_domain` (Text, optional)
- `effort_level` (Text, optional)
