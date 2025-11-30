"""
Tests for job matcher.
"""

import pytest
from src.ai.job_matcher import JobMatcher
from src.db.repository import DatabaseRepository
from src.db.models import EmailModel
from datetime import datetime


@pytest.mark.asyncio
async def test_job_matcher_fuzzy_match():
    """Test fuzzy matching logic."""
    # In production, mock the database repository
    # matcher = JobMatcher(mock_db)

    # Test fuzzy string matching
    from src.ai.job_matcher import JobMatcher
    matcher = object.__new__(JobMatcher)

    score = matcher._fuzzy_match_score("Google Inc", "Google")
    assert score > 0.8

    score = matcher._fuzzy_match_score("Microsoft Corporation", "Microsoft Corp")
    assert score > 0.7


@pytest.mark.asyncio
async def test_job_matcher_timeline_score():
    """Test timeline proximity scoring."""
    matcher = object.__new__(JobMatcher)

    application_date = datetime(2025, 11, 1)
    email_date = datetime(2025, 11, 15)

    score = matcher._timeline_score(application_date, email_date)
    assert 0 < score <= 1.0


if __name__ == "__main__":
    pytest.main([__file__])
