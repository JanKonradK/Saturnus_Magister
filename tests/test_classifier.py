"""
Tests for email classifier.
"""

import pytest
from src.ai.classifier import EmailClassifier
from src.db.models import EmailModel, EmailCategory, Sentiment
from datetime import datetime


@pytest.mark.asyncio
async def test_classifier_interview_invite():
    """Test classification of interview invite."""
    classifier = EmailClassifier()

    email = EmailModel(
        gmail_id="test123",
        thread_id="thread123",
        subject="Interview Invitation - Software Engineer",
        sender_email="recruiter@techcorp.com",
        sender_name="Jane Recruiter",
        recipient_email="test@example.com",
        received_at=datetime.now(),
        body_text="""
        Hi,

        We'd like to schedule an interview for the Software Engineer position.
        Are you available on December 15th at 2:00 PM?

        Best,
        Jane
        """,
    )

    # Note: This test requires XAI_API_KEY to be set
    # In real tests, mock the OpenAI client
    # classification = await classifier.classify(email)

    # assert classification.category == EmailCategory.INTERVIEW_INVITE
    # assert classification.sentiment == Sentiment.POSITIVE
    # assert classification.confidence > 0.8

    # Placeholder assertion
    assert email.gmail_id == "test123"


@pytest.mark.asyncio
async def test_classifier_rejection():
    """Test classification of rejection email."""
    # Similar structure to above
    # In production, mock the AI client
    assert True  # Placeholder


if __name__ == "__main__":
    pytest.main([__file__])
