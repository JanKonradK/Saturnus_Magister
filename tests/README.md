# `tests/` - Test Suite

This directory contains the test suite for Saturnus_Magister.

## Structure

- **`test_classifier.py`**: Tests for `EmailClassifier`. Verifies that emails are correctly categorized and data is extracted.
- **`test_matcher.py`**: Tests for `JobMatcher`. Verifies fuzzy matching logic and timeline scoring.
- **`test_router.py`**: Tests for `TaskRouter`. Verifies Eisenhower Matrix logic and task attribute assignment.

## Running Tests

We use `pytest` as the test runner.

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_router.py

# Run with verbose output
pytest -v
```

## Testing Strategy

### Unit Tests
The current suite focuses on **unit testing** core logic:
- **Routing Logic**: Ensuring an "Interview Invite" goes to Q1, while a "Low Effort Rejection" goes to Q4.
- **Matching Algorithms**: Verifying that "Google Inc" matches "Google" with a high score.
- **Classification Parsing**: Ensuring JSON output from Grok is correctly parsed into Pydantic models.

### Mocking
To avoid API costs and external dependencies during testing, external clients (OpenAI, Gmail, TickTick) should be **mocked**.
- *Note*: The provided tests currently contain placeholders for mocking. In a full CI/CD environment, you would use `unittest.mock` or `pytest-mock` to simulate API responses.

## Future Improvements

- **Integration Tests**: End-to-end tests using a local test database and mocked API endpoints.
- **VCR.py**: Record and replay HTTP interactions for deterministic API testing.
- **Property-based Testing**: Use `hypothesis` to generate edge cases for the matcher.
