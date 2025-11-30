import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Optional
import sys

from src.clients.gmail import GmailClient
from src.clients.ticktick import TickTickClient, EisenhowerQuadrant
from src.ai.classifier import EmailClassifier
from src.ai.job_matcher import JobMatcher
from src.db.repository import Repository
from src.db.models import EmailDirection, EmailCategory, Sentiment, EffortLevel
from src.config import settings

class EmailProcessor:
    """
    Main email processing orchestrator.
    Uses Python 3.14 free-threading for true parallel processing.
    """

    def __init__(self):
        self.gmail = GmailClient()
        self.classifier = EmailClassifier()
        self.ticktick = TickTickClient()
        self.db = Repository()
        self.matcher: Optional[JobMatcher] = None

        # Thread pool for parallel processing
        self.executor = ThreadPoolExecutor(
            max_workers=settings.max_concurrent_emails
        )

    async def initialize(self):
        await self.db.connect()
        self.matcher = JobMatcher(self.db)

        # Verify free-threading is active
        if hasattr(sys, '_is_gil_enabled'):
            gil_status = "DISABLED" if not sys._is_gil_enabled() else "ENABLED"
            print(f"GIL Status: {gil_status}")
            if sys._is_gil_enabled():
                print("⚠️  Running with GIL enabled. Consider using python3.14t")

    async def shutdown(self):
        self.executor.shutdown(wait=True)
        await self.db.close()

    async def process_new_emails(self):
        """
        Fetch and process all new emails.
        Uses free-threading for parallel classification/matching.
        """
        # Fetch emails
        inbound = self.gmail.get_emails(label="INBOX", max_results=50)
        sent = self.gmail.get_emails(label="SENT", max_results=50)

        # Filter unprocessed
        emails_to_process = []
        for email in inbound:
            if not await self.db.is_email_processed(email['id']):
                emails_to_process.append((email, EmailDirection.INBOUND))

        for email in sent:
            if not await self.db.is_email_processed(email['id']):
                emails_to_process.append((email, EmailDirection.OUTBOUND))

        if not emails_to_process:
            print("No new emails to process")
            return

        print(f"Processing {len(emails_to_process)} emails in parallel...")

        # Process in parallel using free-threading
        # Each thread handles: classify → match → route
        loop = asyncio.get_event_loop()

        tasks = [
            loop.run_in_executor(
                self.executor,
                self._process_email_sync,
                email,
                direction
            )
            for email, direction in emails_to_process
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Report results
        success = sum(1 for r in results if not isinstance(r, Exception))
        errors = [r for r in results if isinstance(r, Exception)]

        print(f"Processed {success}/{len(emails_to_process)} emails")
        if errors:
            for e in errors:
                print(f"  Error: {e}")

    def _process_email_sync(self, email: dict, direction: EmailDirection):
        """
        Synchronous email processing (runs in thread).
        This is where free-threading shines - each thread does real work.
        """
        # Need to run async code in thread
        return asyncio.run(self._process_single_email(email, direction))

    async def _process_single_email(self, email: dict, direction: EmailDirection):
        """Process a single email through full pipeline."""

        try:
            # 1. Classify
            analysis = self.classifier.analyze(
                email['subject'],
                email['body'],
                email['sender'] if direction == EmailDirection.INBOUND else email.get('recipient', ''),
                direction
            )

            # 2. Match to job
            matches = await self.matcher.find_matching_jobs(
                analysis,
                email['date'],
                email['sender']
            )

            best_match = matches[0] if matches else None
            requires_review = False

            if best_match:
                if best_match.confidence < settings.auto_match_threshold:
                    requires_review = True
            elif analysis.company_name:
                requires_review = True

            # 3. Get effort level from job
            effort_level = EffortLevel.MEDIUM
            if best_match and not requires_review:
                job = await self.db.get_job_by_id(best_match.job_id)
                if job:
                    effort_level = EffortLevel(job.get('effort_level', 'medium'))

            # 4. Save to database (ALL responses recorded)
            email_db_id = await self.db.save_email({
                'gmail_id': email['id'],
                'thread_id': email['thread_id'],
                'direction': direction.value,
                'sender': email['sender'],
                'recipient': email.get('recipient'),
                'subject': email['subject'],
                'body_text': email['body'],
                'received_at': email['date'],
                'gmail_link': email['link'],
                'category': analysis.category.value,
                'sentiment': analysis.sentiment.value,
                'confidence': analysis.confidence,
                'ai_summary': analysis.summary,
                'extracted_datetime': analysis.extracted_datetime,
                'extracted_deadline': analysis.extracted_deadline,
                'raw_analysis': analysis.model_dump(),
                'processed_at': datetime.utcnow(),
                'matched_job_id': best_match.job_id if best_match and not requires_review else None,
                'match_confidence': best_match.confidence if best_match else None,
                'requires_manual_review': requires_review
            })

            # 5. Queue for review if needed
            if requires_review:
                await self.db.add_to_review_queue(
                    email_db_id,
                    "low_confidence_match" if matches else "no_match_found",
                    [m.model_dump() for m in matches[:5]]
                )

            # 6. Route to TickTick
            await self._route_to_ticktick(
                email_db_id, email, analysis,
                best_match, effort_level, direction
            )

            return {"email_id": email['id'], "status": "success"}

        except Exception as e:
            print(f"Error processing {email['id']}: {e}")
            raise

    async def _route_to_ticktick(
        self,
        email_db_id,
        email: dict,
        analysis,
        match,
        effort_level: EffortLevel,
        direction: EmailDirection
    ):
        """Route email to TickTick: Eisenhower, Work, Calendar, Countdown."""

        # Skip outbound emails for task creation (just record)
        if direction == EmailDirection.OUTBOUND:
            if analysis.category == "sent_availability" and analysis.extracted_datetime:
                await self.ticktick.create_calendar_event(
                    title=f"Proposed Interview: {analysis.company_name or 'Company'}",
                    start_date=analysis.extracted_datetime,
                    content=f"You proposed this time.\n\nEmail: {email['link']}"
                )
            return

        company = analysis.company_name or "Unknown Company"
        position = analysis.position_title or "Position"

        match analysis.category:
            case "interview_invite":
                if analysis.extracted_datetime:
                    results = await self.ticktick.create_interview_entry(
                        company=company,
                        position=position,
                        interview_time=analysis.extracted_datetime,
                        email_link=email['link'],
                        summary=analysis.summary,
                        duration_minutes=analysis.duration_minutes
                    )
                    await self.db.update_email_ticktick_ids(
                        email_db_id,
                        task_id=results.get('eisenhower', {}).get('id'),
                        calendar_event_id=results.get('calendar', {}).get('id')
                    )

            case "assignment":
                if analysis.extracted_deadline:
                    results = await self.ticktick.create_assignment_entry(
                        company=company,
                        position=position,
                        deadline=analysis.extracted_deadline,
                        email_link=email['link'],
                        summary=analysis.summary
                    )
                    await self.db.update_email_ticktick_ids(
                        email_db_id,
                        task_id=results.get('eisenhower', {}).get('id'),
                        calendar_event_id=results.get('calendar', {}).get('id')
                    )

            case "offer":
                priority, tags = self.ticktick.get_priority_and_tags("positive", "offer")
                await self.ticktick.create_eisenhower_task(
                    title=f"🟢 OFFER: {company} - {position}",
                    content=f"{analysis.summary}\n\nEmail: {email['link']}",
                    quadrant=EisenhowerQuadrant.Q1,
                    priority=priority,
                    tags=tags
                )
                await self.ticktick.create_work_task(
                    title=f"Review offer: {company}",
                    content=f"Position: {position}\n\n{analysis.summary}\n\nEmail: {email['link']}",
                    priority=priority,
                    tags=["offer"]
                )

            case "rejection":
                # Always recorded in DB, but only create task if high effort
                result = await self.ticktick.create_rejection_entry(
                    company=company,
                    position=position,
                    email_link=email['link'],
                    summary=analysis.summary,
                    effort_level=effort_level.value
                )
                if result:
                    await self.db.update_email_ticktick_ids(
                        email_db_id,
                        task_id=result.get('id')
                    )

            case "follow_up_needed":
                priority, tags = self.ticktick.get_priority_and_tags(
                    analysis.sentiment.value if hasattr(analysis.sentiment, 'value') else analysis.sentiment,
                    "follow_up_needed"
                )
                await self.ticktick.create_eisenhower_task(
                    title=f"📧 Reply to: {company}",
                    content=f"{analysis.action_required or analysis.summary}\n\nReceived: {email['date']}\nEmail: {email['link']}",
                    quadrant=EisenhowerQuadrant.Q2,
                    priority=priority,
                    tags=tags
                )
                await self.ticktick.create_work_task(
                    title=f"Reply to {company}",
                    content=f"{analysis.action_required or analysis.summary}\n\nEmail: {email['link']}",
                    priority=priority,
                    tags=["reply_needed"]
                )
