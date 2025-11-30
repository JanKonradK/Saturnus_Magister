"""
Email classifier using OpenAI-compatible API.
Determines category, sentiment, and extracts structured data from emails.
"""

import json
from typing import Dict, Any, Optional
from openai import AsyncOpenAI

from src.db.models import EmailModel, EmailClassification, EmailCategory, Sentiment
from src.config import settings


class EmailClassifier:
    """AI-powered email classification."""

    SYSTEM_PROMPT = """Analyze emails and extract structured information.

Extract:
1. **Category**: Email type (interview_invite, assignment, rejection, offer, info, follow_up_needed, unknown)
2. **Sentiment**: positive, negative, or neutral
3. **Confidence**: Classification confidence (0.0-1.0)
4. **Extracted Data**: Dates, deadlines, actionable information

# Category Definitions

## Inbound
- **interview_invite**: Interview scheduling or availability request
- **assignment**: Task with deadline (test, challenge, case study)
- **rejection**: Negative response, position filled
- **offer**: Offer, compensation discussion, intent to hire
- **info**: Status updates, confirmations, no action needed
- **follow_up_needed**: Response required, questions asked
- **unknown**: Cannot confidently categorize

## Outbound
- **sent_application**: Application submission
- **sent_availability**: Proposed times/availability
- **sent_follow_up**: Status inquiry
- **sent_documents**: Document submission
- **info**: General responses, acknowledgments

# Sentiment Rules
- **positive**: Advancement, positive feedback, opportunity
- **negative**: Rejection, cancellation, negative outcome
- **neutral**: Informational, questions, acknowledgments

# Extraction
Extract and format as ISO 8601:
- Dates/times
- Deadlines
- Contact information
- Next steps

Response format (JSON):
{
    "category": "interview_invite",
    "sentiment": "positive",
    "confidence": 0.95,
    "reasoning": "Brief explanation",
    "extracted_data": {
        "date": "2025-12-15T14:00:00Z",
        "deadline": null,
        "contact_name": "Name",
        "meeting_link": "https://...",
        "notes": "Additional context"
    }
}
"""

    USER_PROMPT_TEMPLATE = """Analyze this email:

**Subject**: {subject}
**From**: {sender_name} <{sender_email}>
**Received**: {received_at}

**Body**:
{body}

Classify and extract relevant data."""

    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.agent_api_key,
            base_url=settings.agent_base_url,
        )
        self.model = settings.agent_model

    async def classify(self, email: EmailModel) -> EmailClassification:
        """Classify an email using AI."""
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
