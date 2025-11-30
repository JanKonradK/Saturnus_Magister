"""
Email classifier using Grok 4.1 Fast.
Determines category, sentiment, and extracts structured data from emails.
"""

import json
from typing import Dict, Any, Optional
from openai import AsyncOpenAI

from src.db.models import EmailModel, EmailClassification, EmailCategory, Sentiment
from src.config import settings


class EmailClassifier:
    """Grok-powered email classification."""

    SYSTEM_PROMPT = """You are an expert email classifier for job application responses.

Your task is to analyze emails and extract:
1. **Category**: The type of email (interview_invite, assignment, rejection, offer, info, follow_up_needed, unknown)
2. **Sentiment**: Whether this is positive, negative, or neutral news
3. **Confidence**: Your confidence in the classification (0.0-1.0)
4. **Extracted Data**: Any important dates, deadlines, or actionable information

# Category Definitions

## Inbound Emails
- **interview_invite**: Contains interview date/time or scheduling request. May ask for availability.
- **assignment**: Take-home test, coding challenge, case study with a deadline.
- **rejection**: Application rejected, position filled, or no longer considering candidate.
- **offer**: Job offer, compensation discussion, or intent to hire.
- **info**: Status updates, application confirmations, no immediate action needed.
- **follow_up_needed**: Requires response, asks questions, requests documents or additional information.
- **unknown**: Cannot confidently determine the category.

## Outbound Emails (from user)
- **sent_application**: Job application submission, cover letter.
- **sent_availability**: Response with proposed interview times.
- **sent_follow_up**: Following up on application status.
- **sent_documents**: Sending resume, portfolio, references.
- **info**: Thank you notes, general responses.

# Sentiment Rules
- **positive**: Interview invites, offers, moving to next stage, positive feedback.
- **negative**: Rejections, position filled, application not moving forward.
- **neutral**: Informational updates, acknowledgments, questions.

# Extraction Guidelines
Look for and extract:
- Interview dates/times (format as ISO 8601)
- Assignment deadlines
- Response deadlines ("please reply by...")
- Salary/compensation information
- Next steps mentioned
- Contact information for interviewers

Respond in JSON format:
{
    "category": "interview_invite",
    "sentiment": "positive",
    "confidence": 0.95,
    "reasoning": "Email contains interview scheduling request with specific dates",
    "extracted_data": {
        "interview_date": "2025-12-15T14:00:00Z",
        "interviewer_name": "Jane Smith",
        "meeting_link": "https://...",
        "deadline": null,
        "salary_mentioned": false
    }
}
"""

    USER_PROMPT_TEMPLATE = """Analyze this email:

**Subject**: {subject}
**From**: {sender_name} <{sender_email}>
**Received**: {received_at}

**Body**:
{body}

Classify this email and extract relevant information."""

    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.xai_api_key,
            base_url=settings.xai_base_url,
        )
        self.model = settings.xai_model

    async def classify(self, email: EmailModel) -> EmailClassification:
        """Classify an email using Grok."""
        # Prepare email body
        body = email.body_text or email.body_html or ""
        if len(body) > 10000:
            body = body[:10000] + "\n\n[... truncated ...]"

        # Build prompt
        user_prompt = self.USER_PROMPT_TEMPLATE.format(
            subject=email.subject or "(no subject)",
            sender_name=email.sender_name or "Unknown",
            sender_email=email.sender_email or "unknown@example.com",
            received_at=email.received_at.isoformat(),
            body=body,
        )

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,  # Low temperature for consistent classification
                max_tokens=1000,
                response_format={"type": "json_object"},
            )

            result = json.loads(response.choices[0].message.content)

            return EmailClassification(
                category=EmailCategory(result.get("category", "unknown")),
                sentiment=Sentiment(result.get("sentiment", "neutral")),
                confidence=float(result.get("confidence", 0.5)),
                reasoning=result.get("reasoning"),
                extracted_data=result.get("extracted_data", {}),
            )

        except Exception as e:
            # Fallback to unknown classification
            print(f"Classification error: {e}")
            return EmailClassification(
                category=EmailCategory.UNKNOWN,
                sentiment=Sentiment.NEUTRAL,
                confidence=0.0,
                reasoning=f"Error during classification: {str(e)}",
                extracted_data={},
            )

    async def classify_batch(self, emails: list[EmailModel]) -> list[EmailClassification]:
        """Classify multiple emails concurrently."""
        import asyncio
        tasks = [self.classify(email) for email in emails]
        return await asyncio.gather(*tasks)
