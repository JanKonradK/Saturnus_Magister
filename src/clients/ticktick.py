import httpx
from datetime import datetime, timedelta
from typing import Optional
from enum import Enum
from pydantic import BaseModel
from src.config import settings

class EisenhowerQuadrant(str, Enum):
    Q1 = "q1"  # Urgent + Important
    Q2 = "q2"  # Not Urgent + Important
    Q3 = "q3"  # Urgent + Not Important
    Q4 = "q4"  # Not Urgent + Not Important

class TaskPriority(int, Enum):
    NONE = 0
    LOW = 1
    MEDIUM = 3
    HIGH = 5

class TickTickTask(BaseModel):
    id: Optional[str] = None
    title: str
    content: str = ""
    project_id: str
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None
    tags: list[str] = []
    reminders: list[str] = []  # ["TRIGGER:-PT60M", "TRIGGER:-PT1440M"]

class TickTickCalendarEvent(BaseModel):
    id: Optional[str] = None
    title: str
    start_date: datetime
    end_date: Optional[datetime] = None
    content: str = ""
    is_all_day: bool = False
    reminders: list[str] = ["TRIGGER:-PT60M", "TRIGGER:-PT1440M"]

class TickTickClient:
    """Full TickTick API client with Eisenhower, Work, Calendar, Countdown support."""

    BASE_URL = "https://api.ticktick.com/open/v1"

    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {settings.ticktick_access_token}",
            "Content-Type": "application/json"
        }

        self.quadrant_projects = {
            EisenhowerQuadrant.Q1: settings.ticktick_q1_project,
            EisenhowerQuadrant.Q2: settings.ticktick_q2_project,
            EisenhowerQuadrant.Q3: settings.ticktick_q3_project,
            EisenhowerQuadrant.Q4: settings.ticktick_q4_project,
        }

        self.work_project = settings.ticktick_work_project

    def determine_quadrant(
        self,
        category: str,
        sentiment: str,
        effort_level: str = "medium"
    ) -> EisenhowerQuadrant:
        """Route to Eisenhower quadrant based on rules."""

        # Q1: Urgent + Important
        if category in ("interview_invite", "offer"):
            return EisenhowerQuadrant.Q1

        # Q2: Not Urgent + Important
        if category == "assignment":
            return EisenhowerQuadrant.Q2

        if category == "rejection":
            if effort_level == "high":
                return EisenhowerQuadrant.Q2  # Worth reflecting
            return EisenhowerQuadrant.Q4  # Just record

        if category == "follow_up_needed":
            return EisenhowerQuadrant.Q2

        # Default
        return EisenhowerQuadrant.Q3

    def get_priority_and_tags(
        self,
        sentiment: str,
        category: str
    ) -> tuple[TaskPriority, list[str]]:
        """Color coding via tags and priority."""
        tags = [category]

        if sentiment == "positive":
            tags.append("positive")  # Green
            priority = TaskPriority.HIGH
        elif sentiment == "negative":
            tags.append("negative")  # Red
            priority = TaskPriority.LOW
        else:
            tags.append("neutral")
            priority = TaskPriority.MEDIUM

        return priority, tags

    async def create_task(self, task: TickTickTask) -> dict:
        """Create task in specified project."""
        payload = {
            "title": task.title,
            "content": task.content,
            "projectId": task.project_id,
            "priority": task.priority.value,
        }

        if task.tags:
            payload["tags"] = task.tags

        if task.due_date:
            payload["dueDate"] = task.due_date.strftime("%Y-%m-%dT%H:%M:%S+0000")

        if task.reminders:
            payload["reminders"] = task.reminders

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/task",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()

    async def create_eisenhower_task(
        self,
        title: str,
        content: str,
        quadrant: EisenhowerQuadrant,
        priority: TaskPriority = TaskPriority.MEDIUM,
        tags: list[str] = None,
        due_date: datetime = None
    ) -> dict:
        """Create task in Eisenhower matrix quadrant."""
        task = TickTickTask(
            title=title,
            content=content,
            project_id=self.quadrant_projects[quadrant],
            priority=priority,
            tags=tags or [],
            due_date=due_date
        )
        return await self.create_task(task)

    async def create_work_task(
        self,
        title: str,
        content: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
        tags: list[str] = None,
        due_date: datetime = None
    ) -> dict:
        """Create task in Work list."""
        task = TickTickTask(
            title=title,
            content=content,
            project_id=self.work_project,
            priority=priority,
            tags=tags or [],
            due_date=due_date
        )
        return await self.create_task(task)

    async def create_calendar_event(self, event: TickTickCalendarEvent) -> dict:
        """
        Create calendar event in TickTick.
        This automatically syncs to Google Calendar via TickTick's native integration.
        Also creates countdown for time-sensitive events.
        """
        end_date = event.end_date or (event.start_date + timedelta(hours=1))

        payload = {
            "title": event.title,
            "startDate": event.start_date.strftime("%Y-%m-%dT%H:%M:%S+0000"),
            "endDate": end_date.strftime("%Y-%m-%dT%H:%M:%S+0000"),
            "content": event.content,
            "isAllDay": event.is_all_day,
            "reminders": event.reminders
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/task",  # Calendar events are tasks with dates
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()

    async def create_interview_entry(
        self,
        company: str,
        position: str,
        interview_time: datetime,
        email_link: str,
        summary: str,
        duration_minutes: int = 60
    ) -> dict:
        """
        Create full interview setup:
        1. Calendar event (syncs to Google Calendar + creates countdown)
        2. Eisenhower Q1 task (urgent + important)
        3. Work task for preparation
        """
        results = {}

        # 1. Calendar event with countdown
        event = TickTickCalendarEvent(
            title=f"Interview: {company} - {position}",
            start_date=interview_time,
            end_date=interview_time + timedelta(minutes=duration_minutes),
            content=f"{summary}\n\nEmail: {email_link}",
            reminders=["TRIGGER:-PT1440M", "TRIGGER:-PT60M", "TRIGGER:-PT15M"]
        )
        results["calendar"] = await self.create_calendar_event(event)

        # 2. Eisenhower Q1 task - Reply/confirm
        results["eisenhower"] = await self.create_eisenhower_task(
            title=f"🟢 Confirm: {company} Interview",
            content=f"Position: {position}\n\nReply to confirm attendance\n\nEmail: {email_link}",
            quadrant=EisenhowerQuadrant.Q1,
            priority=TaskPriority.HIGH,
            tags=["positive", "interview_invite"],
            due_date=datetime.now() + timedelta(hours=24)  # Respond within 24h
        )

        # 3. Work task - Prepare
        prep_date = interview_time - timedelta(days=1)
        results["work"] = await self.create_work_task(
            title=f"Prepare for {company} interview",
            content=f"Position: {position}\n\n- Research company\n- Review job description\n- Prepare questions\n\nEmail: {email_link}",
            priority=TaskPriority.HIGH,
            tags=["interview_prep"],
            due_date=prep_date
        )

        return results

    async def create_assignment_entry(
        self,
        company: str,
        position: str,
        deadline: datetime,
        email_link: str,
        summary: str
    ) -> dict:
        """
        Create assignment setup:
        1. Calendar event for deadline (syncs + countdown)
        2. Eisenhower Q2 task (not urgent but important)
        3. Work task
        """
        results = {}

        # 1. Deadline calendar event
        event = TickTickCalendarEvent(
            title=f"⏰ Deadline: {company} Assignment",
            start_date=deadline,
            content=f"Assignment due!\n\n{summary}\n\nEmail: {email_link}",
            reminders=["TRIGGER:-PT1440M", "TRIGGER:-PT180M"]  # 1 day, 3 hours
        )
        results["calendar"] = await self.create_calendar_event(event)

        # 2. Eisenhower Q2 task
        results["eisenhower"] = await self.create_eisenhower_task(
            title=f"🟢 Complete: {company} Assignment",
            content=f"Position: {position}\n\n{summary}\n\nEmail: {email_link}",
            quadrant=EisenhowerQuadrant.Q2,
            priority=TaskPriority.HIGH,
            tags=["positive", "assignment"],
            due_date=deadline - timedelta(hours=12)  # Buffer before deadline
        )

        # 3. Work task
        results["work"] = await self.create_work_task(
            title=f"Complete {company} assignment",
            content=f"Deadline: {deadline.strftime('%Y-%m-%d %H:%M')}\n\n{summary}\n\nEmail: {email_link}",
            priority=TaskPriority.HIGH,
            tags=["assignment"],
            due_date=deadline - timedelta(hours=12)
        )

        return results

    async def create_rejection_entry(
        self,
        company: str,
        position: str,
        email_link: str,
        summary: str,
        effort_level: str
    ) -> Optional[dict]:
        """
        Create rejection entry:
        - High effort: Q2 task (worth reflecting)
        - Low/medium effort: No task (just recorded in DB)
        Always returns None or task info
        """
        if effort_level != "high":
            return None  # Just record in DB, no TickTick task

        return await self.create_eisenhower_task(
            title=f"🔴 Review: {company} Rejection",
            content=f"Position: {position}\n\nHigh effort application.\n\n{summary}\n\nEmail: {email_link}",
            quadrant=EisenhowerQuadrant.Q2,
            priority=TaskPriority.LOW,
            tags=["negative", "rejection", "high_effort"]
        )

    async def get_projects(self) -> list[dict]:
        """Get all projects for setup/debugging."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/project",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
