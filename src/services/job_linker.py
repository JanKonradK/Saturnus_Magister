"""
Job linker service - links emails to Nyx_Venatrix job applications.
Provides high-level orchestration of job matching logic.
"""

from typing import Optional, Tuple
from uuid import UUID

from src.ai.job_matcher import JobMatcher, JobMatchCandidate
from src.db.repository import DatabaseRepository
from src.db.models import EmailModel, EmailJobMatchModel, MatchMethod


class JobLinker:
    """Orchestrates job matching and linking."""

    def __init__(self, db: DatabaseRepository, matcher: JobMatcher):
        self.db = db
        self.matcher = matcher

    async def link_email_to_job(
        self,
        email: EmailModel
    ) -> Tuple[Optional[JobMatchCandidate], bool]:
        """
        Link email to job application.

        Returns:
            (best_match, needs_manual_review)
        """
        return await self.matcher.match_email_to_job(email)

    async def manual_link(
        self,
        email_id: UUID,
        job_id: UUID,
        reviewer_notes: Optional[str] = None,
    ) -> EmailJobMatchModel:
        """
        Manually link email to job (from review queue).

        Returns:
            Created match record
        """
        match = EmailJobMatchModel(
            email_id=email_id,
            job_id=job_id,
            match_score=1.0,  # Manual match = 100% confidence
            match_method=MatchMethod.MANUAL,
            match_signals={"manual": True, "reviewer_notes": reviewer_notes},
            needs_review=False,
            reviewed=True,
            reviewer_notes=reviewer_notes,
        )

        return await self.db.create_match(match)

    async def reject_match(
        self,
        email_id: UUID,
        reviewer_notes: Optional[str] = None,
    ) -> None:
        """
        Reject match - email doesn't relate to any job.
        Update review queue to mark as resolved with no link.
        """
        # Find review queue entry
        reviews = await self.db.get_pending_reviews(limit=100)
        for review in reviews:
            if review.email_id == email_id:
                await self.db.resolve_review(
                    review.id,
                    resolution_action="no_job_link",
                    resolution_notes=reviewer_notes,
                )
                break

    async def get_match_candidates(
        self,
        email: EmailModel,
        limit: int = 10,
    ) -> list[JobMatchCandidate]:
        """Get all potential job match candidates for manual review."""
        return await self.matcher.find_matches(email)
