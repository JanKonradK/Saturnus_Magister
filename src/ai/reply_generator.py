"""
AI-powered email reply generator.
"""

from typing import Optional
from openai import AsyncOpenAI

from src.config import settings
from src.db.models import EmailModel, EmailClassification, EmailCategory

class ReplyGenerator:
    """Generates context-aware email replies."""

    SYSTEM_PROMPT = """You are an executive assistant drafting email replies.
Your goal is to be professional, concise, and polite.

Draft a reply based on the email category:

- **interview_invite**: Thank them, confirm interest. If dates are proposed, say I will check my calendar. If asked for availability, provide placeholders like "[Insert Availability]".
- **assignment**: Acknowledge receipt, confirm I will complete it by the deadline.
- **info/follow_up_needed**: Provide the requested information or acknowledge the update.
- **rejection**: Professional thank you for the opportunity.

Keep it short. Do not include subject lines or placeholders unless necessary.
Sign off as "Best regards," followed by "[My Name]".
"""

    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.agent_api_key,
            base_url=settings.agent_base_url,
        )
        self.model = settings.agent_model

    async def generate_draft(self, email: EmailModel, classification: EmailClassification) -> Optional[str]:
        """Generate a draft reply body."""

        # Only reply to specific categories
        if classification.category not in [
            EmailCategory.INTERVIEW_INVITE,
            EmailCategory.ASSIGNMENT,
            EmailCategory.FOLLOW_UP_NEEDED
        ]:
            return None

        prompt = f"""
        Incoming Email:
        From: {email.sender_name}
        Subject: {email.subject}
        Body: {email.body_text[:2000]}

        Category: {classification.category.value}
        Context: {classification.reasoning}

        Draft a reply:
        """

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=500,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating reply: {e}")
            return None
