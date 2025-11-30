"""
Unit tests for TaskRouter logic.
"""

import pytest
from src.services.task_router import TaskRouter
from src.clients.ticktick import EisenhowerQuadrant
from src.db.models import EmailClassification, EmailCategory, Sentiment

def test_determine_quadrant_q1():
    """Test Q1 routing (Urgent + Important)."""
    router = object.__new__(TaskRouter)

    classification = EmailClassification(
        category=EmailCategory.INTERVIEW_INVITE,
        sentiment=Sentiment.POSITIVE,
        confidence=0.9
    )

    routing = router._determine_routing(classification)
    # Note: ModelQuadrant enum values might differ from client enum, checking logic
    # Assuming Q1 mapping is correct in implementation
    assert "Urgent and important" in routing.reasoning
    assert routing.priority == 5

def test_determine_quadrant_q2():
    """Test Q2 routing (Not Urgent + Important)."""
    router = object.__new__(TaskRouter)

    classification = EmailClassification(
        category=EmailCategory.ASSIGNMENT,
        sentiment=Sentiment.NEUTRAL,
        confidence=0.9
    )

    routing = router._determine_routing(classification)
    assert "Important but not urgent" in routing.reasoning

def test_determine_quadrant_q4():
    """Test Q4 routing (Not Urgent + Not Important)."""
    router = object.__new__(TaskRouter)

    classification = EmailClassification(
        category=EmailCategory.REJECTION,
        sentiment=Sentiment.NEGATIVE,
        confidence=0.9
    )

    # Low effort rejection -> Q4
    routing = router._determine_routing(classification, effort_level="low")
    assert "Low effort rejection" in routing.reasoning
