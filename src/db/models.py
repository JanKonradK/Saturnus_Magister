"""
Pydantic models for Saturnus_Magister database entities.
Provides type-safe data validation and ORM-like functionality.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, Field, EmailStr, field_validator


class EmailCategory(str, Enum):
    """Email classification categories."""
    # Inbound
    INTERVIEW_INVITE = "interview_invite"
    ASSIGNMENT = "assignment"
    REJECTION = "rejection"
    OFFER = "offer"
    INFO = "info"
    FOLLOW_UP_NEEDED = "follow_up_needed"
    UNKNOWN = "unknown"

    # Outbound
    SENT_APPLICATION = "sent_application"
    SENT_AVAILABILITY = "sent_availability"
    SENT_FOLLOW_UP = "sent_follow_up"
    SENT_DOCUMENTS = "sent_documents"


class Sentiment(str, Enum):
    """Email sentiment classification."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class MatchMethod(str, Enum):
    """How email-job match was determined."""
    AUTO = "auto"
    MANUAL = "manual"
    AI_DISAMBIGUATION = "ai_disambiguation"


class TaskType(str, Enum):
    """Type of TickTick task."""
    TASK = "task"
    CALENDAR_EVENT = "calendar_event"
    COUNTDOWN = "countdown"


class ReviewStatus(str, Enum):
    """Manual review queue status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


# Database Models

class EmailModel(BaseModel):
    """Email storage model."""
    id: Optional[UUID] = None
    gmail_id: str
    thread_id: str
    subject: Optional[str] = None
    sender_email: Optional[str] = None
    sender_name: Optional[str] = None
    recipient_email: Optional[str] = None
    received_at: datetime
    body_text: Optional[str] = None
    body_html: Optional[str] = None

    # Classification
    category: Optional[EmailCategory] = None
    sentiment: Optional[Sentiment] = None
    confidence: Optional[float] = None

    # Processing
    processed: bool = False
    processed_at: Optional[datetime] = None
    error: Optional[str] = None

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        use_enum_values = True


class EmailJobMatchModel(BaseModel):
    """Email-to-job matching model."""
    id: Optional[UUID] = None
    email_id: UUID
    job_id: Optional[UUID] = None

    # Matching
    match_score: float = Field(ge=0.0, le=1.0)
    match_method: MatchMethod
    match_signals: Optional[Dict[str, Any]] = None

    # Review
    needs_review: bool = False
    reviewed: bool = False
    reviewed_at: Optional[datetime] = None
    reviewer_notes: Optional[str] = None

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        use_enum_values = True


class TickTickTaskModel(BaseModel):
    """TickTick task tracking model."""
    id: Optional[UUID] = None
    email_id: UUID

    # TickTick metadata
    ticktick_task_id: Optional[str] = None
    ticktick_project_id: str

    # Task details
    title: str
    content: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: int = Field(ge=0, le=5, default=3)
    tags: List[str] = Field(default_factory=list)

    # Task type
    task_type: TaskType = TaskType.TASK

    # Calendar event fields
    is_calendar_event: bool = False
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_all_day: bool = False
    reminders: List[str] = Field(default_factory=list)
    countdown_enabled: bool = False

    # Sync status
    synced: bool = False
    synced_at: Optional[datetime] = None
    sync_error: Optional[str] = None

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        use_enum_values = True


class ManualReviewQueueModel(BaseModel):
    """Manual review queue entry."""
    id: Optional[UUID] = None
    email_id: UUID

    # Review reason
    reason: str
    reason_details: Optional[Dict[str, Any]] = None

    # Status
    status: ReviewStatus = ReviewStatus.PENDING
    assigned_to: Optional[str] = None

    # Resolution
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolution_action: Optional[str] = None
    resolution_notes: Optional[str] = None

    # Priority
    priority: int = Field(ge=1, le=10, default=5)

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        use_enum_values = True


class CompanyBlocklistModel(BaseModel):
    """Company blocklist entry."""
    id: Optional[UUID] = None
    company_name: str
    domain: Optional[str] = None

    # Metadata
    reason: Optional[str] = None
    rejection_count: int = 0

    # Status
    blocked: bool = True
    blocked_at: Optional[datetime] = None
    unblocked_at: Optional[datetime] = None

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ResponseAnalyticsModel(BaseModel):
    """Response analytics tracking."""
    id: Optional[UUID] = None
    email_id: UUID
    job_id: Optional[UUID] = None

    # Response metadata
    response_type: str
    response_stage: Optional[str] = None

    # Company info
    company_name: Optional[str] = None
    position_title: Optional[str] = None

    # Effort tracking
    effort_level: Optional[str] = None
    had_feedback: bool = False

    # Timeline
    application_date: Optional[datetime] = None
    response_date: Optional[datetime] = None
    days_to_response: Optional[int] = None

    # Timestamp
    created_at: Optional[datetime] = None


# API/Transfer Models

class EmailClassification(BaseModel):
    """AI classification result."""
    category: EmailCategory
    sentiment: Sentiment
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: Optional[str] = None
    extracted_data: Optional[Dict[str, Any]] = None  # Dates, deadlines, etc.


class JobMatchCandidate(BaseModel):
    """Potential job match candidate."""
    job_id: UUID
    company_name: str
    position_title: str
    match_score: float = Field(ge=0.0, le=1.0)
    match_signals: Dict[str, Any]

    # From Nyx_Venatrix
    application_date: Optional[datetime] = None
    effort_level: Optional[str] = None


class EisenhowerQuadrant(str, Enum):
    """Eisenhower matrix quadrants."""
    Q1_URGENT_IMPORTANT = "q1"
    Q2_NOT_URGENT_IMPORTANT = "q2"
    Q3_URGENT_NOT_IMPORTANT = "q3"
    Q4_NOT_URGENT_NOT_IMPORTANT = "q4"


class TaskRoutingDecision(BaseModel):
    """Task routing decision."""
    quadrant: EisenhowerQuadrant
    create_calendar_event: bool = False
    enable_countdown: bool = False
    priority: int = Field(ge=0, le=5)
    tags: List[str] = Field(default_factory=list)
    reminders: List[str] = Field(default_factory=list)
    reasoning: Optional[str] = None
