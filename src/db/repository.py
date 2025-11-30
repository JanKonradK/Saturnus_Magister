"""
Async database repository for Saturnus_Magister.
Provides CRUD operations and business logic queries.
"""

import asyncpg
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from .models import (
    EmailModel,
    EmailJobMatchModel,
    TickTickTaskModel,
    ManualReviewQueueModel,
    CompanyBlocklistModel,
    ResponseAnalyticsModel,
)


class DatabaseRepository:
    """Async PostgreSQL repository."""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool: Optional[asyncpg.Pool] = None

    async def initialize(self) -> None:
        """Initialize connection pool."""
        self.pool = await asyncpg.create_pool(
            self.database_url,
            min_size=2,
            max_size=10,
            command_timeout=60,
        )

    async def close(self) -> None:
        """Close connection pool."""
        if self.pool:
            await self.pool.close()

    @asynccontextmanager
    async def transaction(self):
        """Context manager for transactions."""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                yield conn

    # Email operations

    async def get_email_by_gmail_id(self, gmail_id: str) -> Optional[EmailModel]:
        """Get email by Gmail ID."""
        query = "SELECT * FROM emails WHERE gmail_id = $1"
        row = await self.pool.fetchrow(query, gmail_id)
        return EmailModel(**dict(row)) if row else None

    async def create_email(self, email: EmailModel) -> EmailModel:
        """Create new email record."""
        query = """
            INSERT INTO emails (
                gmail_id, thread_id, subject, sender_email, sender_name,
                recipient_email, received_at, body_text, body_html,
                category, sentiment, confidence
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            RETURNING *
        """
        row = await self.pool.fetchrow(
            query,
            email.gmail_id,
            email.thread_id,
            email.subject,
            email.sender_email,
            email.sender_name,
            email.recipient_email,
            email.received_at,
            email.body_text,
            email.body_html,
            email.category,
            email.sentiment,
            email.confidence,
        )
        return EmailModel(**dict(row))

    async def update_email_classification(
        self,
        email_id: UUID,
        category: str,
        sentiment: str,
        confidence: float,
    ) -> None:
        """Update email classification."""
        query = """
            UPDATE emails
            SET category = $2, sentiment = $3, confidence = $4, updated_at = NOW()
            WHERE id = $1
        """
        await self.pool.execute(query, email_id, category, sentiment, confidence)

    async def mark_email_processed(self, email_id: UUID, error: Optional[str] = None) -> None:
        """Mark email as processed."""
        query = """
            UPDATE emails
            SET processed = TRUE, processed_at = NOW(), error = $2, updated_at = NOW()
            WHERE id = $1
        """
        await self.pool.execute(query, email_id, error)

    async def get_unprocessed_emails(self, limit: int = 50) -> List[EmailModel]:
        """Get unprocessed emails."""
        query = """
            SELECT * FROM emails
            WHERE processed = FALSE
            ORDER BY received_at ASC
            LIMIT $1
        """
        rows = await self.pool.fetch(query, limit)
        return [EmailModel(**dict(row)) for row in rows]

    # Email-job matching operations

    async def create_match(self, match: EmailJobMatchModel) -> EmailJobMatchModel:
        """Create email-job match."""
        query = """
            INSERT INTO email_job_matches (
                email_id, job_id, match_score, match_method, match_signals,
                needs_review
            ) VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING *
        """
        row = await self.pool.fetchrow(
            query,
            match.email_id,
            match.job_id,
            match.match_score,
            match.match_method,
            match.match_signals,
            match.needs_review,
        )
        return EmailJobMatchModel(**dict(row))

    async def get_matches_for_email(self, email_id: UUID) -> List[EmailJobMatchModel]:
        """Get all matches for an email."""
        query = "SELECT * FROM email_job_matches WHERE email_id = $1 ORDER BY match_score DESC"
        rows = await self.pool.fetch(query, email_id)
        return [EmailJobMatchModel(**dict(row)) for row in rows]

    async def update_match_review(
        self,
        match_id: UUID,
        reviewed: bool,
        reviewer_notes: Optional[str] = None,
    ) -> None:
        """Update match review status."""
        query = """
            UPDATE email_job_matches
            SET reviewed = $2, reviewed_at = NOW(), reviewer_notes = $3, updated_at = NOW()
            WHERE id = $1
        """
        await self.pool.execute(query, match_id, reviewed, reviewer_notes)

    # TickTick task operations

    async def create_task(self, task: TickTickTaskModel) -> TickTickTaskModel:
        """Create TickTick task record."""
        query = """
            INSERT INTO ticktick_tasks (
                email_id, ticktick_project_id, title, content, due_date, priority, tags,
                task_type, is_calendar_event, start_time, end_time, is_all_day,
                reminders, countdown_enabled
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
            RETURNING *
        """
        row = await self.pool.fetchrow(
            query,
            task.email_id,
            task.ticktick_project_id,
            task.title,
            task.content,
            task.due_date,
            task.priority,
            task.tags,
            task.task_type,
            task.is_calendar_event,
            task.start_time,
            task.end_time,
            task.is_all_day,
            task.reminders,
            task.countdown_enabled,
        )
        return TickTickTaskModel(**dict(row))

    async def mark_task_synced(
        self,
        task_id: UUID,
        ticktick_task_id: str,
        error: Optional[str] = None,
    ) -> None:
        """Mark task as synced to TickTick."""
        query = """
            UPDATE ticktick_tasks
            SET synced = TRUE, synced_at = NOW(), ticktick_task_id = $2, sync_error = $3, updated_at = NOW()
            WHERE id = $1
        """
        await self.pool.execute(query, task_id, ticktick_task_id, error)

    async def get_unsynced_tasks(self, limit: int = 50) -> List[TickTickTaskModel]:
        """Get unsynced tasks."""
        query = """
            SELECT * FROM ticktick_tasks
            WHERE synced = FALSE
            ORDER BY created_at ASC
            LIMIT $1
        """
        rows = await self.pool.fetch(query, limit)
        return [TickTickTaskModel(**dict(row)) for row in rows]

    # Manual review queue operations

    async def add_to_review_queue(self, review: ManualReviewQueueModel) -> ManualReviewQueueModel:
        """Add email to manual review queue."""
        query = """
            INSERT INTO manual_review_queue (
                email_id, reason, reason_details, priority
            ) VALUES ($1, $2, $3, $4)
            RETURNING *
        """
        row = await self.pool.fetchrow(
            query,
            review.email_id,
            review.reason,
            review.reason_details,
            review.priority,
        )
        return ManualReviewQueueModel(**dict(row))

    async def get_pending_reviews(self, limit: int = 50) -> List[ManualReviewQueueModel]:
        """Get pending reviews."""
        query = """
            SELECT * FROM manual_review_queue
            WHERE resolved = FALSE
            ORDER BY priority DESC, created_at ASC
            LIMIT $1
        """
        rows = await self.pool.fetch(query, limit)
        return [ManualReviewQueueModel(**dict(row)) for row in rows]

    async def resolve_review(
        self,
        review_id: UUID,
        resolution_action: str,
        resolution_notes: Optional[str] = None,
    ) -> None:
        """Resolve manual review."""
        query = """
            UPDATE manual_review_queue
            SET resolved = TRUE, resolved_at = NOW(), resolution_action = $2,
                resolution_notes = $3, status = 'completed', updated_at = NOW()
            WHERE id = $1
        """
        await self.pool.execute(query, review_id, resolution_action, resolution_notes)

    # Company blocklist operations

    async def is_company_blocked(self, company_name: str, domain: Optional[str] = None) -> bool:
        """Check if company is blocked."""
        if domain:
            query = """
                SELECT EXISTS(
                    SELECT 1 FROM company_blocklist
                    WHERE blocked = TRUE AND (company_name = $1 OR domain = $2)
                )
            """
            return await self.pool.fetchval(query, company_name, domain)
        else:
            query = """
                SELECT EXISTS(
                    SELECT 1 FROM company_blocklist
                    WHERE blocked = TRUE AND company_name = $1
                )
            """
            return await self.pool.fetchval(query, company_name)

    async def add_to_blocklist(self, blocklist: CompanyBlocklistModel) -> CompanyBlocklistModel:
        """Add company to blocklist."""
        query = """
            INSERT INTO company_blocklist (company_name, domain, reason, rejection_count)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (company_name, domain) DO UPDATE
            SET blocked = TRUE, blocked_at = NOW(), reason = $3, rejection_count = company_blocklist.rejection_count + 1
            RETURNING *
        """
        row = await self.pool.fetchrow(
            query,
            blocklist.company_name,
            blocklist.domain,
            blocklist.reason,
            blocklist.rejection_count,
        )
        return CompanyBlocklistModel(**dict(row))

    # Analytics operations

    async def record_response(self, analytics: ResponseAnalyticsModel) -> ResponseAnalyticsModel:
        """Record response for analytics."""
        query = """
            INSERT INTO response_analytics (
                email_id, job_id, response_type, response_stage, company_name,
                position_title, effort_level, had_feedback, application_date,
                response_date, days_to_response
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            RETURNING *
        """
        row = await self.pool.fetchrow(
            query,
            analytics.email_id,
            analytics.job_id,
            analytics.response_type,
            analytics.response_stage,
            analytics.company_name,
            analytics.position_title,
            analytics.effort_level,
            analytics.had_feedback,
            analytics.application_date,
            analytics.response_date,
            analytics.days_to_response,
        )
        return ResponseAnalyticsModel(**dict(row))

    async def get_company_rejection_count(self, company_name: str, days: int = 365) -> int:
        """Get rejection count for company within timeframe."""
        query = """
            SELECT COUNT(*) FROM response_analytics
            WHERE company_name = $1
            AND response_type = 'rejection'
            AND created_at > NOW() - INTERVAL '%s days'
        """ % days
        return await self.pool.fetchval(query, company_name)

    async def get_success_rate_by_company(self) -> List[Dict[str, Any]]:
        """Get success rate analytics by company."""
        query = """
            SELECT
                company_name,
                COUNT(*) as total_responses,
                SUM(CASE WHEN response_type IN ('interview', 'offer') THEN 1 ELSE 0 END) as positive_responses,
                SUM(CASE WHEN response_type = 'rejection' THEN 1 ELSE 0 END) as rejections,
                ROUND(
                    SUM(CASE WHEN response_type IN ('interview', 'offer') THEN 1 ELSE 0 END)::numeric /
                    COUNT(*)::numeric * 100,
                    2
                ) as success_rate
            FROM response_analytics
            WHERE company_name IS NOT NULL
            GROUP BY company_name
            ORDER BY success_rate DESC, total_responses DESC
        """
        rows = await self.pool.fetch(query)
        return [dict(row) for row in rows]

    # Processing state operations

    async def get_state(self, key: str) -> Optional[str]:
        """Get processing state value."""
        query = "SELECT state_value FROM processing_state WHERE state_key = $1"
        return await self.pool.fetchval(query, key)

    async def set_state(self, key: str, value: str) -> None:
        """Set processing state value."""
        query = """
            INSERT INTO processing_state (state_key, state_value)
            VALUES ($1, $2)
            ON CONFLICT (state_key) DO UPDATE
            SET state_value = $2, updated_at = NOW()
        """
        await self.pool.execute(query, key, value)

    # Nyx_Venatrix integration (assumes shared database)

    async def get_recent_job_applications(self, days: int = 90) -> List[Dict[str, Any]]:
        """Get recent job applications from Nyx_Venatrix."""
        # This assumes applied_jobs table exists in the same database
        # Adjust table/column names based on actual Nyx_Venatrix schema
        query = """
            SELECT
                id as job_id,
                company_name,
                position_title,
                applied_at,
                job_url,
                company_domain,
                effort_level
            FROM applied_jobs
            WHERE applied_at > NOW() - INTERVAL '%s days'
            ORDER BY applied_at DESC
        """ % days
        try:
            rows = await self.pool.fetch(query)
            return [dict(row) for row in rows]
        except Exception:
            # Table might not exist yet, return empty list
            return []

    async def get_job_by_id(self, job_id: UUID) -> Optional[Dict[str, Any]]:
        """Get job application details from Nyx_Venatrix."""
        query = """
            SELECT * FROM applied_jobs WHERE id = $1
        """
        try:
            row = await self.pool.fetchrow(query, job_id)
            return dict(row) if row else None
        except Exception:
            return None
