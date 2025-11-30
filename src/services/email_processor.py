"""
Main email processing orchestrator for Saturnus_Magister.
Coordinates Gmail monitoring, classification, job matching, and TickTick routing.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID

from src.clients.gmail import GmailClient
from src.clients.ticktick import TickTickClient
from src.ai.classifier import EmailClassifier
from src.ai.job_matcher import JobMatcher
from src.db.repository import DatabaseRepository
from src.db.models import (
    EmailModel,
    EmailJobMatchModel,
    TickTickTaskModel,
    ManualReviewQueueModel,
    ResponseAnalyticsModel,
    EmailCategory,
    Sentiment,
    MatchMethod,
)
from src.services.task_router import TaskRouter
from src.services.job_linker import JobLinker
from src.config import settings


class EmailProcessor:
    """Main orchestrator for email processing pipeline."""

    def __init__(self):
        self.gmail_client = GmailClient()
        self.ticktick_client = TickTickClient()
        self.classifier = EmailClassifier()
        self.db: Optional[DatabaseRepository] = None
        self.job_matcher: Optional[JobMatcher] = None
        self.task_router: Optional[TaskRouter] = None
        self.job_linker: Optional[JobLinker] = None

    async def initialize(self) -> None:
        """Initialize all components."""
        # Database
        self.db = DatabaseRepository(settings.database_url)
        await self.db.initialize()

        # Gmail
        self.gmail_client.authenticate()

        # Job matcher (needs DB)
        self.job_matcher = JobMatcher(self.db)

        # Task router
        self.task_router = TaskRouter(self.db, self.ticktick_client)

        # Job linker
        self.job_linker = JobLinker(self.db, self.job_matcher)

        print("✓ Saturnus_Magister initialized")

    async def shutdown(self) -> None:
        """Cleanup resources."""
        if self.db:
            await self.db.close()
        print("✓ Shutdown complete")

    async def process_new_emails(self) -> dict:
        """
        Main processing loop:
        1. Fetch new emails from Gmail (inbox + sent)
        2. Classify with Grok
        3. Match to Nyx_Venatrix jobs
        4. Route to TickTick
        5. Record analytics

        Returns:
            Processing statistics
        """
        stats = {
            "inbox_processed": 0,
            "sent_processed": 0,
            "matched": 0,
            "needs_review": 0,
            "errors": 0,
        }

        # Process inbox
        print("Fetching inbox emails...")
        inbox_emails = await self.gmail_client.get_inbox_messages(
            max_results=50,
            only_unread=False  # Process all to catch up
        )

        for email in inbox_emails:
            try:
                # Check if already processed
                existing = await self.db.get_email_by_gmail_id(email.gmail_id)
                if existing and existing.processed:
                    continue

                await self._process_inbound_email(email)
                stats["inbox_processed"] += 1

            except Exception as e:
                print(f"Error processing email {email.gmail_id}: {e}")
                stats["errors"] += 1

        # Process sent folder
        print("Fetching sent emails...")
        sent_emails = await self.gmail_client.get_sent_messages(max_results=50)

        for email in sent_emails:
            try:
                existing = await self.db.get_email_by_gmail_id(email.gmail_id)
                if existing and existing.processed:
                    continue

                await self._process_outbound_email(email)
                stats["sent_processed"] += 1

            except Exception as e:
                print(f"Error processing sent email {email.gmail_id}: {e}")
                stats["errors"] += 1

        print(f"\nProcessing complete: {stats}")
        return stats

    async def _process_inbound_email(self, email: EmailModel) -> None:
        """Process inbound email (from companies/recruiters)."""
        # 1. Classify with Grok
        print(f"  Classifying: {email.subject}")
        classification = await self.classifier.classify(email)

        email.category = classification.category
        email.sentiment = classification.sentiment
        email.confidence = classification.confidence

        # 2. Save email to database
        saved_email = await self.db.create_email(email)

        # 3. Match to job application
        best_match, needs_review = await self.job_matcher.match_email_to_job(email)

        if best_match:
            # Save match
            match = EmailJobMatchModel(
                email_id=saved_email.id,
                job_id=best_match.job_id,
                match_score=best_match.match_score,
                match_method=MatchMethod.AUTO if not needs_review else MatchMethod.AI_DISAMBIGUATION,
                match_signals=best_match.match_signals,
                needs_review=needs_review,
            )
            await self.db.create_match(match)

            # Get job details from Nyx_Venatrix
            job_details = await self.db.get_job_by_id(best_match.job_id)
            effort_level = job_details.get("effort_level") if job_details else None
        else:
            effort_level = None
            needs_review = True

        # 4. Queue for manual review if needed
        if needs_review:
            reason = "no_match_found" if not best_match else "low_confidence_match"
            if classification.category == EmailCategory.UNKNOWN:
                reason = "ambiguous_category"

            await self.db.add_to_review_queue(
                ManualReviewQueueModel(
                    email_id=saved_email.id,
                    reason=reason,
                    reason_details={
                        "classification": classification.dict(),
                        "best_match": best_match.dict() if best_match else None,
                    },
                    priority=8 if classification.category in [
                        EmailCategory.INTERVIEW_INVITE,
                        EmailCategory.OFFER
                    ] else 5,
                )
            )

        # 5. Record analytics (ALL responses)
        if classification.category in [
            EmailCategory.REJECTION,
            EmailCategory.INTERVIEW_INVITE,
            EmailCategory.OFFER,
        ]:
            analytics = ResponseAnalyticsModel(
                email_id=saved_email.id,
                job_id=best_match.job_id if best_match else None,
                response_type=classification.category.value,
                response_stage="unknown",  # Could be extracted from email
                company_name=best_match.company_name if best_match else None,
                position_title=best_match.position_title if best_match else None,
                effort_level=effort_level,
                had_feedback=False,  # TODO: Extract from classification
                application_date=best_match.application_date if best_match else None,
                response_date=email.received_at.date(),
                days_to_response=(
                    (email.received_at.date() - best_match.application_date.date()).days
                    if best_match and best_match.application_date else None
                ),
            )
            await self.db.record_response(analytics)

            # Check if company should be blocked (high rejection rate)
            if classification.category == EmailCategory.REJECTION and best_match:
                rejection_count = await self.db.get_company_rejection_count(
                    best_match.company_name,
                    days=365
                )
                if rejection_count >= 3:
                    print(f"⚠️  Company {best_match.company_name} has {rejection_count} rejections")

        # 6. Route to TickTick (unless needs review)
        if not needs_review or classification.category in [
            EmailCategory.INTERVIEW_INVITE,
            EmailCategory.OFFER
        ]:
            await self.task_router.route_email(
                email=saved_email,
                classification=classification,
                job_match=best_match,
                effort_level=effort_level,
            )

        # 7. Mark as processed
        await self.db.mark_email_processed(saved_email.id, error=None)
        print(f"  ✓ {classification.category.value} ({classification.sentiment.value})")

    async def _process_outbound_email(self, email: EmailModel) -> None:
        """Process outbound email (sent by user)."""
        # Classify
        classification = await self.classifier.classify(email)

        email.category = classification.category
        email.sentiment = classification.sentiment
        email.confidence = classification.confidence

        # Save
        saved_email = await self.db.create_email(email)

        # Outbound emails: try to match to job but don't require manual review
        best_match, _ = await self.job_matcher.match_email_to_job(email)

        if best_match:
            match = EmailJobMatchModel(
                email_id=saved_email.id,
                job_id=best_match.job_id,
                match_score=best_match.match_score,
                match_method=MatchMethod.AUTO,
                match_signals=best_match.match_signals,
                needs_review=False,
            )
            await self.db.create_match(match)

        # For sent availability/interview times, create calendar placeholder
        if classification.category == EmailCategory.SENT_AVAILABILITY:
            if classification.extracted_data and "proposed_times" in classification.extracted_data:
                # Create calendar events for proposed times
                for proposed_time in classification.extracted_data["proposed_times"][:3]:
                    try:
                        start_time = datetime.fromisoformat(proposed_time)
                        await self.task_router._create_calendar_placeholder(
                            saved_email.id,
                            f"Proposed: {best_match.company_name if best_match else 'Interview'}",
                            start_time,
                        )
                    except Exception:
                        pass

        # Mark as processed
        await self.db.mark_email_processed(saved_email.id)
        print(f"  ✓ Sent: {classification.category.value}")

    async def sync_ticktick_tasks(self) -> int:
        """Sync unsynced tasks to TickTick."""
        unsynced = await self.db.get_unsynced_tasks(limit=50)

        synced_count = 0
        for task in unsynced:
            try:
                if task.is_calendar_event:
                    # Create calendar event
                    from src.clients.ticktick import TickTickCalendarEvent
                    event = TickTickCalendarEvent(
                        title=task.title,
                        start_date=task.start_time,
                        end_date=task.end_time,
                        content=task.content,
                        is_all_day=task.is_all_day,
                        reminders=task.reminders,
                    )
                    result = await self.ticktick_client.create_calendar_event(event)
                else:
                    # Create task
                    from src.clients.ticktick import TickTickTask, TaskPriority
                    tt_task = TickTickTask(
                        title=task.title,
                        content=task.content,
                        project_id=task.ticktick_project_id,
                        priority=TaskPriority(task.priority),
                        due_date=task.due_date,
                        tags=task.tags,
                        reminders=task.reminders,
                    )
                    result = await self.ticktick_client.create_task(tt_task)

                # Mark as synced
                await self.db.mark_task_synced(
                    task.id,
                    ticktick_task_id=result.get("id"),
                    error=None,
                )
                synced_count += 1

            except Exception as e:
                print(f"Error syncing task {task.id}: {e}")
                await self.db.mark_task_synced(task.id, ticktick_task_id=None, error=str(e))

        if synced_count > 0:
            print(f"✓ Synced {synced_count} tasks to TickTick")

        return synced_count
