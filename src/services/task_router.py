"""
Task router for Eisenhower matrix + Work + Calendar routing.
Determines how to route emails to TickTick based on category, sentiment, and urgency.
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from src.clients.ticktick import TickTickClient, EisenhowerQuadrant, TaskPriority
from src.db.repository import DatabaseRepository
from src.db.models import (
    EmailModel,
    EmailClassification,
    JobMatchCandidate,
    TickTickTaskModel,
    EmailCategory,
    Sentiment,
    TaskType,
    EisenhowerQuadrant as ModelQuadrant,
    TaskRoutingDecision,
)


class TaskRouter:
    """Routes emails to appropriate TickTick destinations."""

    def __init__(self, db: DatabaseRepository, ticktick: TickTickClient):
        self.db = db
        self.ticktick = ticktick

    def _determine_routing(
        self,
        classification: EmailClassification,
        effort_level: Optional[str] = None,
    ) -> TaskRoutingDecision:
        """
        Determine Eisenhower quadrant and task properties.

        Eisenhower Matrix:
        - Q1 (Urgent + Important): interview_invite, offer
        - Q2 (Not Urgent + Important): assignment, follow_up_needed, high-effort rejection
        - Q3 (Urgent + Not Important): info_requires_ack
        - Q4 (Not Urgent + Not Important): low-effort rejection
        """
        category = classification.category
        sentiment = classification.sentiment

        # Default values
        quadrant = ModelQuadrant.Q3_URGENT_NOT_IMPORTANT
        create_calendar = False
        enable_countdown = False
        priority = 3
        tags = [category.value]
        reminders = []
        reasoning = ""

        # Q1: Urgent + Important
        if category in [EmailCategory.INTERVIEW_INVITE, EmailCategory.OFFER]:
            quadrant = ModelQuadrant.Q1_URGENT_IMPORTANT
            priority = 5
            create_calendar = bool(classification.extracted_data and
                                   classification.extracted_data.get("interview_date"))
            enable_countdown = create_calendar
            reminders = ["-1d", "-1h", "-15m"] if create_calendar else ["-1d"]
            reasoning = "Urgent and important - requires immediate attention"

        # Q2: Not Urgent + Important
        elif category == EmailCategory.ASSIGNMENT:
            quadrant = ModelQuadrant.Q2_NOT_URGENT_IMPORTANT
            priority = 4
            create_calendar = bool(classification.extracted_data and
                                   classification.extracted_data.get("deadline"))
            enable_countdown = create_calendar
            reminders = ["-1d", "-3h"] if create_calendar else []
            reasoning = "Important but not urgent - schedule properly"

        elif category == EmailCategory.FOLLOW_UP_NEEDED:
            quadrant = ModelQuadrant.Q2_NOT_URGENT_IMPORTANT
            priority = 3
            reminders = ["-1d"]
            reasoning = "Requires response but not urgent"

        elif category == EmailCategory.REJECTION:
            if effort_level == "high":
                quadrant = ModelQuadrant.Q2_NOT_URGENT_IMPORTANT
                priority = 2
                reasoning = "High effort rejection - worth reflecting on"
            else:
                quadrant = ModelQuadrant.Q4_NOT_URGENT_NOT_IMPORTANT
                priority = 1
                reasoning = "Low effort rejection - just recording"

        # Q3: Urgent + Not Important (default for INFO that needs acknowledgment)
        elif category == EmailCategory.INFO:
            quadrant = ModelQuadrant.Q3_URGENT_NOT_IMPORTANT
            priority = 2
            reasoning = "Informational - quick acknowledgment may be needed"

        # Add sentiment tag
        if sentiment == Sentiment.POSITIVE:
            tags.append("positive")
            if priority < 5:
                priority += 1  # Bump priority for positive emails
        elif sentiment == Sentiment.NEGATIVE:
            tags.append("negative")
        else:
            tags.append("neutral")

        return TaskRoutingDecision(
            quadrant=quadrant,
            create_calendar_event=create_calendar,
            enable_countdown=enable_countdown,
            priority=priority,
            tags=tags,
            reminders=reminders,
            reasoning=reasoning,
        )

    async def route_email(
        self,
        email: EmailModel,
        classification: EmailClassification,
        job_match: Optional[JobMatchCandidate] = None,
        effort_level: Optional[str] = None,
    ) -> list[TickTickTaskModel]:
        """
        Route email to TickTick.

        Returns:
            List of created tasks
        """
        routing = self._determine_routing(classification, effort_level)

        # Extract company and position
        company = job_match.company_name if job_match else "Unknown Company"
        position = job_match.position_title if job_match else "Position"

        # Build email link
        email_link = f"https://mail.google.com/mail/u/0/#all/{email.gmail_id}"

        created_tasks = []

        # Create calendar event if needed
        if routing.create_calendar_event:
            calendar_task = await self._create_calendar_event(
                email_id=email.id,
                classification=classification,
                company=company,
                position=position,
                email_link=email_link,
                reminders=routing.reminders,
                enable_countdown=routing.enable_countdown,
            )
            if calendar_task:
                created_tasks.append(calendar_task)

        # Create Eisenhower task (unless rejection with low effort)
        if not (classification.category == EmailCategory.REJECTION and effort_level != "high"):
            eisenhower_task = await self._create_eisenhower_task(
                email_id=email.id,
                classification=classification,
                quadrant=routing.quadrant,
                company=company,
                position=position,
                email_link=email_link,
                priority=routing.priority,
                tags=routing.tags,
            )
            created_tasks.append(eisenhower_task)

        # Create Work task for actionable items
        if classification.category in [
            EmailCategory.INTERVIEW_INVITE,
            EmailCategory.ASSIGNMENT,
            EmailCategory.FOLLOW_UP_NEEDED,
        ]:
            work_task = await self._create_work_task(
                email_id=email.id,
                classification=classification,
                company=company,
                position=position,
                email_link=email_link,
                priority=routing.priority,
                tags=routing.tags,
            )
            created_tasks.append(work_task)

        return created_tasks

    async def _create_calendar_event(
        self,
        email_id: UUID,
        classification: EmailClassification,
        company: str,
        position: str,
        email_link: str,
        reminders: list[str],
        enable_countdown: bool,
    ) -> Optional[TickTickTaskModel]:
        """Create calendar event for interview or deadline."""
        extracted_data = classification.extracted_data or {}

        # Get datetime
        event_time = None
        if "interview_date" in extracted_data:
            event_time = datetime.fromisoformat(extracted_data["interview_date"])
        elif "deadline" in extracted_data:
            event_time = datetime.fromisoformat(extracted_data["deadline"])

        if not event_time:
            return None

        # Determine duration
        is_deadline = classification.category == EmailCategory.ASSIGNMENT
        duration = timedelta(hours=1) if not is_deadline else timedelta(minutes=0)

        # Build title
        prefix = "⏰ Deadline:" if is_deadline else "📅 Interview:"
        title = f"{prefix} {company} - {position}"

        # Build content
        content = f"{classification.reasoning or ''}\n\nEmail: {email_link}"

        # Create task model
        task = TickTickTaskModel(
            email_id=email_id,
            ticktick_project_id=self.ticktick.work_project,  # Calendar events go to work project
            title=title,
            content=content,
            task_type=TaskType.CALENDAR_EVENT,
            is_calendar_event=True,
            start_time=event_time,
            end_time=event_time + duration if not is_deadline else event_time,
            is_all_day=is_deadline,
            reminders=reminders,
            countdown_enabled=enable_countdown,
            priority=5,
            tags=["calendar", classification.category.value],
        )

        # Save to DB
        return await self.db.create_task(task)

    async def _create_eisenhower_task(
        self,
        email_id: UUID,
        classification: EmailClassification,
        quadrant: ModelQuadrant,
        company: str,
        position: str,
        email_link: str,
        priority: int,
        tags: list[str],
    ) -> TickTickTaskModel:
        """Create task in Eisenhower matrix."""
        # Map quadrant to project
        project_map = {
            ModelQuadrant.Q1_URGENT_IMPORTANT: self.ticktick.quadrant_projects[EisenhowerQuadrant.Q1],
            ModelQuadrant.Q2_NOT_URGENT_IMPORTANT: self.ticktick.quadrant_projects[EisenhowerQuadrant.Q2],
            ModelQuadrant.Q3_URGENT_NOT_IMPORTANT: self.ticktick.quadrant_projects[EisenhowerQuadrant.Q3],
            ModelQuadrant.Q4_NOT_URGENT_NOT_IMPORTANT: self.ticktick.quadrant_projects[EisenhowerQuadrant.Q4],
        }

        # Build title with emoji
        emoji = {
            EmailCategory.INTERVIEW_INVITE: "🟢",
            EmailCategory.OFFER: "🟢",
            EmailCategory.ASSIGNMENT: "🟢",
            EmailCategory.REJECTION: "🔴",
            EmailCategory.FOLLOW_UP_NEEDED: "📧",
            EmailCategory.INFO: "ℹ️",
        }.get(classification.category, "📋")

        title = f"{emoji} {classification.category.value.replace('_', ' ').title()}: {company}"

        # Build content
        content = f"**Position:** {position}\n\n"
        content += f"{classification.reasoning or ''}\n\n"
        content += f"**Email:** {email_link}"

        # Determine due date
        due_date = None
        if classification.category == EmailCategory.INTERVIEW_INVITE:
            due_date = datetime.now() + timedelta(hours=24)  # Respond within 24h
        elif classification.category == EmailCategory.FOLLOW_UP_NEEDED:
            due_date = datetime.now() + timedelta(days=2)

        # Create task
        task = TickTickTaskModel(
            email_id=email_id,
            ticktick_project_id=project_map[quadrant],
            title=title,
            content=content,
            task_type=TaskType.TASK,
            priority=priority,
            tags=tags,
            due_date=due_date,
        )

        return await self.db.create_task(task)

    async def _create_work_task(
        self,
        email_id: UUID,
        classification: EmailClassification,
        company: str,
        position: str,
        email_link: str,
        priority: int,
        tags: list[str],
    ) -> TickTickTaskModel:
        """Create task in Work list."""
        # Build title
        action_map = {
            EmailCategory.INTERVIEW_INVITE: f"Prepare for {company} interview",
            EmailCategory.ASSIGNMENT: f"Complete {company} assignment",
            EmailCategory.FOLLOW_UP_NEEDED: f"Reply to {company}",
        }
        title = action_map.get(classification.category, f"Action: {company}")

        # Build content
        content = f"**Position:** {position}\n\n"

        if classification.category == EmailCategory.INTERVIEW_INVITE:
            content += "- Research company\n"
            content += "- Review job description\n"
            content += "- Prepare questions\n"
            content += "- Test technology (Zoom/Teams)\n\n"
        elif classification.category == EmailCategory.ASSIGNMENT:
            content += f"{classification.reasoning or ''}\n\n"
            if classification.extracted_data and "deadline" in classification.extracted_data:
                deadline_str = classification.extracted_data["deadline"]
                content += f"**Deadline:** {deadline_str}\n\n"

        content += f"**Email:** {email_link}"

        # Due date
        due_date = None
        extracted_data = classification.extracted_data or {}

        if "interview_date" in extracted_data:
            interview_time = datetime.fromisoformat(extracted_data["interview_date"])
            due_date = interview_time - timedelta(days=1)  # Day before interview
        elif "deadline" in extracted_data:
            deadline_time = datetime.fromisoformat(extracted_data["deadline"])
            due_date = deadline_time - timedelta(hours=12)  # Buffer before deadline

        # Create task
        task = TickTickTaskModel(
            email_id=email_id,
            ticktick_project_id=self.ticktick.work_project,
            title=title,
            content=content,
            task_type=TaskType.TASK,
            priority=priority,
            tags=tags + ["work"],
            due_date=due_date,
        )

        return await self.db.create_task(task)

    async def _create_calendar_placeholder(
        self,
        email_id: UUID,
        title: str,
        start_time: datetime,
    ) -> TickTickTaskModel:
        """Create placeholder calendar event (for proposed times)."""
        task = TickTickTaskModel(
            email_id=email_id,
            ticktick_project_id=self.ticktick.work_project,
            title=title,
            content="Proposed time - awaiting confirmation",
            task_type=TaskType.CALENDAR_EVENT,
            is_calendar_event=True,
            start_time=start_time,
            end_time=start_time + timedelta(hours=1),
            is_all_day=False,
            reminders=[],
            priority=3,
            tags=["proposed"],
        )

        return await self.db.create_task(task)
