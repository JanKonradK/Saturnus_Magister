"""
Job matcher using fuzzy matching + AI disambiguation.
Links emails to Nyx_Venatrix job applications with confidence scoring.
"""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID
from rapidfuzz import fuzz
from openai import AsyncOpenAI

from src.db.models import EmailModel, JobMatchCandidate
from src.db.repository import DatabaseRepository
from src.config import settings


class JobMatcher:
    """Matches emails to Nyx_Venatrix job applications."""

    # Matching weights
    COMPANY_NAME_WEIGHT = 0.4
    DOMAIN_WEIGHT = 0.2
    POSITION_WEIGHT = 0.3
    TIMELINE_WEIGHT = 0.1

    # Timeline matching
    TIMELINE_WINDOW_DAYS = 90  # Consider jobs applied within 90 days

    AI_DISAMBIGUATION_PROMPT = """You are a job application matching expert. Given an email and multiple potential job application matches, determine which job application this email is most likely referring to.

Email context:
- Subject: {subject}
- From: {sender_email}
- Body excerpt: {body_excerpt}

Candidate matches:
{candidates}

Analyze the email content and re-rank the candidates. Consider:
1. Company name mentions in email vs application
2. Position title mentions
3. Email domain matching company domain
4. Timeline (more recent applications more likely for ongoing processes)
5. Any unique identifiers (job IDs, application numbers, etc.)

Respond in JSON format with re-ranked candidates:
{{
    "best_match_job_id": "uuid",
    "confidence": 0.95,
    "reasoning": "Email domain matches and recent application",
    "ranked_candidates": [
        {{"job_id": "uuid", "score": 0.95, "reason": "..."}},
        {{"job_id": "uuid", "score": 0.60, "reason": "..."}}
    ]
}}
"""

    def __init__(self, repository: DatabaseRepository):
        self.repository = repository
        self.client = AsyncOpenAI(
            api_key=settings.xai_api_key,
            base_url=settings.xai_base_url,
        )

    def _extract_domain(self, email: str) -> Optional[str]:
        """Extract domain from email address."""
        try:
            return email.split("@")[1].lower() if "@" in email else None
        except Exception:
            return None

    def _fuzzy_match_score(self, a: str, b: str) -> float:
        """Fuzzy string matching score (0.0-1.0)."""
        if not a or not b:
            return 0.0
        return fuzz.ratio(a.lower(), b.lower()) / 100.0

    def _timeline_score(self, application_date: datetime, email_date: datetime) -> float:
        """Score based on timeline proximity."""
        days_diff = abs((email_date - application_date).days)

        # Within 90 days = good
        if days_diff <= self.TIMELINE_WINDOW_DAYS:
            # Linear decay from 1.0 to 0.0 over 90 days
            return 1.0 - (days_diff / self.TIMELINE_WINDOW_DAYS)
        else:
            return 0.0

    async def find_matches(self, email: EmailModel) -> List[JobMatchCandidate]:
        """Find potential job matches for an email."""
        # Get recent job applications from Nyx_Venatrix
        jobs = await self.repository.get_recent_job_applications(
            days=self.TIMELINE_WINDOW_DAYS
        )

        if not jobs:
            return []

        # Extract email domain
        sender_domain = self._extract_domain(email.sender_email or "")

        # Extract company and position mentions from email
        email_text = (email.subject or "") + " " + (email.body_text or "")

        candidates = []

        for job in jobs:
            signals = {}
            total_score = 0.0

            # Company name fuzzy match
            company_score = 0.0
            if job.get("company_name"):
                company_score = self._fuzzy_match_score(
                    job["company_name"],
                    email_text[:500]  # Check first 500 chars
                )
                signals["company_name_fuzzy"] = company_score
                total_score += company_score * self.COMPANY_NAME_WEIGHT

            # Email domain match
            domain_score = 0.0
            if sender_domain and job.get("company_domain"):
                # Check if domains match or sender domain contains company domain
                if sender_domain == job["company_domain"] or \
                   job["company_domain"] in sender_domain:
                    domain_score = 1.0
                signals["domain_match"] = domain_score
                total_score += domain_score * self.DOMAIN_WEIGHT

            # Position title fuzzy match
            position_score = 0.0
            if job.get("position_title"):
                position_score = self._fuzzy_match_score(
                    job["position_title"],
                    email_text[:500]
                )
                signals["position_title_fuzzy"] = position_score
                total_score += position_score * self.POSITION_WEIGHT

            # Timeline proximity
            timeline_score = 0.0
            if job.get("applied_at"):
                timeline_score = self._timeline_score(
                    job["applied_at"],
                    email.received_at
                )
                signals["timeline_proximity"] = timeline_score
                total_score += timeline_score * self.TIMELINE_WEIGHT

            # Only include if some signal matched
            if total_score > 0.1:
                candidates.append(JobMatchCandidate(
                    job_id=job["job_id"],
                    company_name=job.get("company_name", "Unknown"),
                    position_title=job.get("position_title", "Unknown"),
                    match_score=total_score,
                    match_signals=signals,
                    application_date=job.get("applied_at"),
                    effort_level=job.get("effort_level"),
                ))

        # Sort by match score
        candidates.sort(key=lambda x: x.match_score, reverse=True)

        return candidates

    async def disambiguate_with_ai(
        self,
        email: EmailModel,
        candidates: List[JobMatchCandidate],
    ) -> Optional[JobMatchCandidate]:
        """Use AI to disambiguate between multiple close matches."""
        if len(candidates) < 2:
            return candidates[0] if candidates else None

        # Prepare candidates for AI
        candidates_text = "\n".join([
            f"- Job {i+1}: {c.company_name} - {c.position_title} (Match Score: {c.match_score:.2f}, Applied: {c.application_date})"
            for i, c in enumerate(candidates[:5])  # Top 5 only
        ])

        # Create prompt
        body_excerpt = (email.body_text or email.body_html or "")[:1000]
        prompt = self.AI_DISAMBIGUATION_PROMPT.format(
            subject=email.subject or "(no subject)",
            sender_email=email.sender_email or "unknown",
            body_excerpt=body_excerpt,
            candidates=candidates_text,
        )

        try:
            response = await self.client.chat.completions.create(
                model=settings.xai_model,
                messages=[
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=1000,
                response_format={"type": "json_object"},
            )

            result = json.loads(response.choices[0].message.content)

            # Find the job in our candidates
            best_job_id = UUID(result.get("best_match_job_id"))
            for candidate in candidates:
                if candidate.job_id == best_job_id:
                    # Update score with AI confidence
                    candidate.match_score = max(
                        candidate.match_score,
                        result.get("confidence", candidate.match_score)
                    )
                    candidate.match_signals["ai_reasoning"] = result.get("reasoning", "")
                    return candidate

            # Fallback to top candidate if AI didn't help
            return candidates[0]

        except Exception as e:
            print(f"AI disambiguation error: {e}")
            # Fallback to top fuzzy match
            return candidates[0]

    async def match_email_to_job(self, email: EmailModel) -> tuple[Optional[JobMatchCandidate], bool]:
        """
        Match email to job application.

        Returns:
            (best_match, needs_manual_review)
        """
        candidates = await self.find_matches(email)

        if not candidates:
            # No matches found
            return None, True  # Needs review

        top_match = candidates[0]

        # Auto-match threshold
        if top_match.match_score >= settings.auto_match_threshold:
            return top_match, False

        # Check if multiple close matches (ambiguous)
        if len(candidates) > 1:
            second_score = candidates[1].match_score
            if abs(top_match.match_score - second_score) < 0.15:
                # Close scores, use AI disambiguation
                best_match = await self.disambiguate_with_ai(email, candidates)

                # If AI gives high confidence, auto-match
                if best_match and best_match.match_score >= settings.auto_match_threshold:
                    return best_match, False
                else:
                    return best_match, True  # Needs manual review

        # Between review threshold and auto threshold
        if top_match.match_score >= settings.review_threshold:
            return top_match, True  # Needs review

        # Below review threshold
        return top_match, True  # Low confidence, needs review
