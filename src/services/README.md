# `src/services/` - Business Logic & Orchestration

This module contains the core business logic that ties together AI, Database, and API Clients.

## Components

### `email_processor.py` - Main Orchestrator

The central nervous system of Saturnus_Magister. It coordinates the entire processing pipeline.

**Responsibilities**:
1. **Fetching**: Polls Gmail for new messages (Inbox & Sent).
2. **Classification**: Sends emails to `EmailClassifier` (Grok).
3. **Matching**: delegates to `JobMatcher` to find Nyx_Venatrix jobs.
4. **Routing**: Uses `TaskRouter` to determine TickTick actions.
5. **Analytics**: Records outcomes in the database.
6. **Syncing**: Ensures tasks are successfully created in TickTick.

**Flow**:
```python
async def process_new_emails(self):
    emails = gmail.get_unread()
    for email in emails:
        classification = await classifier.classify(email)
        match = await matcher.match(email)

        if match.needs_review:
            await db.queue_for_review(email, match)
        else:
            await router.route_email(email, classification, match)
```

### `task_router.py` - Eisenhower Logic

Determines *how* an email should be represented in TickTick based on its category, sentiment, and urgency.

**Logic**:
- **Eisenhower Matrix**: Maps emails to Q1-Q4 quadrants.
- **Calendar Events**: Creates events for `interview_invite` (with date) and `assignment` (with deadline).
- **Work Tasks**: Creates actionable items in the "Work" project for things like "Prepare for interview".
- **Prioritization**: Assigns priority (High/Med/Low) and tags (e.g., `#positive`, `#interview`).

**Routing Rules**:
- **Q1**: Interviews, Offers.
- **Q2**: Assignments, Important Follow-ups.
- **Q3**: Quick Info/Acks.
- **Q4**: Low-value Rejections.

### `job_linker.py` - Job Linking Service

Manages the relationship between emails and job applications, specifically handling manual interventions.

**Responsibilities**:
- **Manual Linking**: Processes decisions from the Manual Review Queue.
- **Rejection**: Handles "No Match" decisions.
- **Candidate Retrieval**: Fetches potential matches for the UI.

## Design Patterns

- **Dependency Injection**: Services receive their dependencies (DB, Clients) in `__init__`, making them easy to test.
- **Orchestrator Pattern**: `EmailProcessor` directs the flow, while specialized services handle specific domain logic.
- **Idempotency**: The system is designed to handle restarts gracefully. Processed emails are flagged in the DB to prevent duplicate processing.

## Usage

```python
from src.services.email_processor import EmailProcessor

processor = EmailProcessor()
await processor.initialize()

# Run one processing cycle
stats = await processor.process_new_emails()

await processor.shutdown()
```
