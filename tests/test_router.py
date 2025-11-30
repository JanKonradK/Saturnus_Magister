"""
Tests for task router (Eisenhower logic).
"""

import pytest
from src.services.task_router import TaskRouter
from src.db.models import EmailCategory, Sentiment, EmailClassification, EisenhowerQuadrant


def test_eisenhower_routing_q1():
    """Test Q1 routing (Urgent + Important)."""
    classification = EmailClassification(
        category=EmailCategory.INTERVIEW_INVITE,
        sentiment=Sentiment.POSITIVE,
        confidence=0.95,
    )

    router = object.__new__(TaskRouter)
    routing = router._determine_routing(classification)

    assert routing.quadrant == EisenhowerQuadrant.Q1_URGENT_IMPORTANT
    assert routing.priority >= 4


def test_eisenhower_routing_q2():
    """Test Q2 routing (Not Urgent + Important)."""
    classification = EmailClassification(
        category=EmailCategory.ASSIGNMENT,
        sentiment=Sentiment.POSITIVE,
        confidence=0.90,
    )

    router = object.__new__(TaskRouter)
    routing = router._determine_routing(classification)

    assert routing.quadrant == EisenhowerQuadrant.Q2_NOT_URGENT_IMPORTANT


def test_eisenhower_routing_rejection_high_effort():
    """Test rejection routing based on effort level."""
    classification = EmailClassification(
        category=EmailCategory.REJECTION,
        sentiment=Sentiment.NEGATIVE,
        confidence=0.95,
    )

    router = object.__new__(TaskRouter)

    # High effort → Q2
    routing = router._determine_routing(classification, effort_level="high")
    assert routing.quadrant == EisenhowerQuadrant.Q2_NOT_URGENT_IMPORTANT

    # Low effort → Q4
    routing = router._determine_routing(classification, effort_level="low")
    assert routing.quadrant == EisenhowerQuadrant.Q4_NOT_URGENT_NOT_IMPORTANT


if __name__ == "__main__":
    pytest.main([__file__])
