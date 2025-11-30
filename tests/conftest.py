"""
Pytest fixtures for Saturnus_Magister.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from src.db.models import EmailModel, EmailCategory, Sentiment

@pytest.fixture
def sample_email():
    """Create a sample email model."""
    return EmailModel(
        gmail_id="test_gmail_id_123",
        thread_id="test_thread_id_123",
        subject="Interview Invitation - Software Engineer",
        sender_email="recruiter@techcorp.com",
        sender_name="Jane Recruiter",
        recipient_email="me@example.com",
        received_at=datetime.now(),
        body_text="Hi, we'd like to schedule an interview. Are you free next Tuesday?",
        body_html="<p>Hi, we'd like to schedule an interview...</p>"
    )

@pytest.fixture
def mock_openai():
    """Mock OpenAI client."""
    mock = AsyncMock()
    # Default successful response
    mock.chat.completions.create.return_value = MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(
                    content='{"category": "interview_invite", "sentiment": "positive", "confidence": 0.95, "reasoning": "Clear invite", "extracted_data": {"interview_date": "2025-12-01T14:00:00"}}'
                )
            )
        ]
    )
    return mock

@pytest.fixture
def mock_db():
    """Mock database repository."""
    mock = AsyncMock()
    return mock
