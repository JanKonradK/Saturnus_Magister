"""
Simulation script for Saturnus_Magister.
Runs the full pipeline with mocked components to demonstrate functionality.
"""

import asyncio
import sys
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import MagicMock, AsyncMock, patch

from rich.console import Console
from rich.panel import Panel

from src.db.models import EmailModel, EmailCategory, Sentiment, EmailClassification, JobMatchCandidate
from src.services.email_processor import EmailProcessor
from src.clients.ticktick import EisenhowerQuadrant

console = Console()

# --- Mock Data ---

MOCK_EMAILS = [
    EmailModel(
        gmail_id="sim_1", thread_id="t1", subject="Interview with TechCorp",
        sender_email="recruiter@techcorp.com", recipient_email="me@example.com",
        received_at=datetime.now(),
        body_text="Hi, we'd like to schedule an interview for the Senior Engineer role."
    ),
    EmailModel(
        gmail_id="sim_2", thread_id="t2", subject="Application Update - StartupInc",
        sender_email="no-reply@startupinc.com", recipient_email="me@example.com",
        received_at=datetime.now(),
        body_text="Thank you for applying. Unfortunately we are not moving forward."
    ),
    EmailModel(
        gmail_id="sim_3", thread_id="t3", subject="Coding Challenge",
        sender_email="hiring@unicorn.io", recipient_email="me@example.com",
        received_at=datetime.now(),
        body_text="Here is your take-home assignment. Due in 48 hours."
    )
]

MOCK_CLASSIFICATIONS = {
    "sim_1": EmailClassification(
        category=EmailCategory.INTERVIEW_INVITE,
        sentiment=Sentiment.POSITIVE,
        confidence=0.98,
        extracted_data={"company": "TechCorp", "position": "Senior Engineer"}
    ),
    "sim_2": EmailClassification(
        category=EmailCategory.REJECTION,
        sentiment=Sentiment.NEGATIVE,
        confidence=0.99,
        extracted_data={"company": "StartupInc"}
    ),
    "sim_3": EmailClassification(
        category=EmailCategory.ASSIGNMENT,
        sentiment=Sentiment.NEUTRAL,
        confidence=0.95,
        extracted_data={"company": "Unicorn.io", "deadline": (datetime.now() + timedelta(days=2)).isoformat()}
    )
}

MOCK_MATCHES = {
    "sim_1": JobMatchCandidate(
        job_id=uuid4(), company_name="TechCorp", position_title="Senior Engineer",
        match_score=0.95, match_signals={"company": 1.0}, application_date=datetime.now()
    ),
    "sim_2": JobMatchCandidate(
        job_id=uuid4(), company_name="StartupInc", position_title="Backend Dev",
        match_score=0.92, match_signals={"company": 1.0}, application_date=datetime.now()
    ),
    "sim_3": JobMatchCandidate(
        job_id=uuid4(), company_name="Unicorn.io", position_title="Full Stack",
        match_score=0.90, match_signals={"company": 1.0}, application_date=datetime.now()
    )
}

# --- Mock Classes ---

class MockGmailClient:
    async def get_inbox_messages(self, **kwargs):
        console.print("[dim]📧 MockGmail: Fetching inbox...[/dim]")
        await asyncio.sleep(0.5)
        return MOCK_EMAILS

    async def get_sent_messages(self, **kwargs):
        return []

    def authenticate(self):
        pass

class MockClassifier:
    async def classify(self, email):
        console.print(f"[dim]🧠 MockGrok: Classifying '{email.subject}'...[/dim]")
        await asyncio.sleep(0.3)
        return MOCK_CLASSIFICATIONS.get(email.gmail_id)

class MockJobMatcher:
    def __init__(self, db): pass
    async def match_email_to_job(self, email):
        console.print(f"[dim]🔗 MockMatcher: Linking '{email.subject}'...[/dim]")
        match = MOCK_MATCHES.get(email.gmail_id)
        return match, False  # match, needs_review

class MockTickTickClient:
    quadrant_projects = {
        EisenhowerQuadrant.Q1: "proj_Q1",
        EisenhowerQuadrant.Q2: "proj_Q2",
        EisenhowerQuadrant.Q3: "proj_Q3",
        EisenhowerQuadrant.Q4: "proj_Q4"
    }
    work_project = "proj_work"

    async def create_task(self, task):
        console.print(f"[bold green]✓ TickTick: Created Task[/bold green] -> [cyan]{task.title}[/cyan] (Priority: {task.priority})")
        return {"id": "mock_task_id"}

    async def create_calendar_event(self, event):
        console.print(f"[bold green]✓ TickTick: Created Event[/bold green] -> [cyan]{event.title}[/cyan]")
        return {"id": "mock_event_id"}

class MockDB:
    async def initialize(self): pass
    async def close(self): pass
    async def get_email_by_gmail_id(self, gid): return None
    async def create_email(self, email):
        # Assign a UUID to the email
        email.id = uuid4()
        return email
    async def create_match(self, match): pass
    async def get_job_by_id(self, jid): return {"effort_level": "medium"}
    async def record_response(self, analytics): pass
    async def mark_email_processed(self, eid, error=None): pass
    async def create_task(self, task): return task # Return task as if saved
    async def get_unsynced_tasks(self, limit): return [] # Skip sync loop for sim
    async def get_company_rejection_count(self, company, days): return 0
    async def add_to_review_queue(self, review): pass

# --- Simulation Runner ---

async def run_simulation():
    console.print(Panel.fit("[bold yellow]Saturnus_Magister Simulation[/bold yellow]\nRunning full pipeline with MOCKED services", border_style="yellow"))

    # Patch everything!
    with patch('src.services.email_processor.GmailClient', return_value=MockGmailClient()), \
         patch('src.services.email_processor.EmailClassifier', return_value=MockClassifier()), \
         patch('src.services.email_processor.JobMatcher', MockJobMatcher), \
         patch('src.services.email_processor.TickTickClient', return_value=MockTickTickClient()), \
         patch('src.services.email_processor.DatabaseRepository', return_value=MockDB()), \
         patch('src.services.task_router.TickTickClient', return_value=MockTickTickClient()):

        processor = EmailProcessor()
        await processor.initialize()

        # Inject mock DB into router manually since processor init creates it
        processor.db = MockDB()
        processor.task_router.db = MockDB()

        console.print("\n[bold]🚀 Starting Processing Cycle...[/bold]\n")

        stats = await processor.process_new_emails()

        console.print("\n[bold]📊 Simulation Stats:[/bold]")
        console.print(stats)

        console.print("\n[bold green]✨ Simulation Complete![/bold green]")

if __name__ == "__main__":
    asyncio.run(run_simulation())
