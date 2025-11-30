"""
Unit tests for JobMatcher logic.
"""

import pytest
from datetime import datetime, timedelta
from src.ai.job_matcher import JobMatcher

@pytest.mark.asyncio
async def test_fuzzy_match_score():
    """Test fuzzy string matching."""
    matcher = object.__new__(JobMatcher)

    # Exact match
    assert matcher._fuzzy_match_score("Google", "Google") == 1.0

    # Partial match
    score = matcher._fuzzy_match_score("Google Inc", "Google")
    assert score > 0.8

    # No match
    assert matcher._fuzzy_match_score("Apple", "Google") < 0.5

@pytest.mark.asyncio
async def test_timeline_score():
    """Test timeline proximity scoring."""
    matcher = object.__new__(JobMatcher)

    now = datetime.now()

    # Same day = 1.0
    assert matcher._timeline_score(now, now) == 1.0

    # 45 days ago = ~0.5 (linear decay over 90 days)
    past = now - timedelta(days=45)
    score = matcher._timeline_score(past, now)
    assert 0.4 < score < 0.6

    # 100 days ago = 0.0
    ancient = now - timedelta(days=100)
    assert matcher._timeline_score(ancient, now) == 0.0
