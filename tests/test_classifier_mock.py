"""
Unit tests for EmailClassifier using mocks.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from src.ai.classifier import EmailClassifier
from src.db.models import EmailCategory, Sentiment

@pytest.mark.asyncio
async def test_classify_interview_invite(sample_email, mock_openai):
    """Test that valid JSON response is parsed correctly."""

    with patch("src.ai.classifier.AsyncOpenAI", return_value=mock_openai):
        classifier = EmailClassifier()
        # Inject the mock client directly to bypass __init__ creation if needed
        classifier.client = mock_openai

        result = await classifier.classify(sample_email)

        assert result.category == EmailCategory.INTERVIEW_INVITE
        assert result.sentiment == Sentiment.POSITIVE
        assert result.confidence == 0.95
        assert result.extracted_data["interview_date"] == "2025-12-01T14:00:00"

@pytest.mark.asyncio
async def test_classify_json_error(sample_email, mock_openai):
    """Test handling of malformed JSON from AI."""

    # Mock a bad response
    mock_openai.chat.completions.create.return_value.choices[0].message.content = "Not JSON"

    with patch("src.ai.classifier.AsyncOpenAI", return_value=mock_openai):
        classifier = EmailClassifier()
        classifier.client = mock_openai

        result = await classifier.classify(sample_email)

        # Should fallback to UNKNOWN
        assert result.category == EmailCategory.UNKNOWN
        assert result.confidence == 0.0

@pytest.mark.asyncio
async def test_classify_api_error(sample_email, mock_openai):
    """Test handling of API errors."""

    mock_openai.chat.completions.create.side_effect = Exception("API Error")

    with patch("src.ai.classifier.AsyncOpenAI", return_value=mock_openai):
        classifier = EmailClassifier()
        classifier.client = mock_openai

        result = await classifier.classify(sample_email)

        assert result.category == EmailCategory.UNKNOWN
        assert result.confidence == 0.0
