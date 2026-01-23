"""
Shared pytest fixtures for Schema Builder tests.
"""

import pytest
from typing import List, Dict, Any

from src.domain.interfaces import IAIService
from src.bl.builder import SchemaBuilderService
from src.bl.scoring.engine.scoring_engine import ScoringEngine
from src.bl.analyzer import SchemaAnalyzer
from src.bl.validator import SchemaValidator


class MockAIService(IAIService):
    """Mock AI service for testing without external API calls."""

    def __init__(self, regex_response: str | None = None, score_response: int | None = 99):
        self._regex_response = regex_response
        self._score_response = score_response
        self.generate_regex_calls: List[List[str]] = []
        self.evaluate_schema_calls: List[Dict[str, Any]] = []

    async def generate_regex(self, samples: List[str]) -> str | None:
        self.generate_regex_calls.append(samples)
        # Return specific patterns based on sample content
        if samples and "ABC" in samples[0]:
            return r"^ABC-\d+$"
        return self._regex_response

    async def evaluate_schema(self, schema: Dict[str, Any]) -> int | None:
        self.evaluate_schema_calls.append(schema)
        return self._score_response


class FailingAIService(IAIService):
    """AI service that always raises exceptions for error testing."""

    async def generate_regex(self, samples: List[str]) -> str | None:
        raise Exception("AI service unavailable")

    async def evaluate_schema(self, schema: Dict[str, Any]) -> int | None:
        raise Exception("AI service unavailable")


@pytest.fixture
def mock_ai_service():
    """Provides a mock AI service instance."""
    return MockAIService()


@pytest.fixture
def failing_ai_service():
    """Provides a failing AI service for error testing."""
    return FailingAIService()


@pytest.fixture
def schema_service(mock_ai_service):
    """Provides a SchemaBuilderService with mocked AI."""
    return SchemaBuilderService(ai_service=mock_ai_service)


@pytest.fixture
def schema_service_no_ai():
    """Provides a SchemaBuilderService without AI."""
    return SchemaBuilderService(ai_service=None)


@pytest.fixture
def scoring_engine():
    """Provides a ScoringEngine instance."""
    return ScoringEngine()


@pytest.fixture
def schema_analyzer():
    """Provides a SchemaAnalyzer instance."""
    return SchemaAnalyzer()


@pytest.fixture
def schema_validator():
    """Provides a SchemaValidator instance."""
    return SchemaValidator()


# Sample data fixtures


@pytest.fixture
def simple_object():
    """Simple flat object for basic testing."""
    return {"name": "John", "age": 30}


@pytest.fixture
def nested_object():
    """Nested object for complex testing."""
    return {
        "user": {
            "name": "John",
            "email": "john@example.com",
            "address": {"street": "123 Main St", "city": "NYC"},
        },
        "active": True,
    }


@pytest.fixture
def array_of_objects():
    """Array of similar objects for merge testing."""
    return [
        {"name": "John", "age": 30},
        {"name": "Jane", "age": 25},
        {"name": "Bob", "age": 35},
    ]


@pytest.fixture
def mixed_array():
    """Array with mixed types for anyOf testing."""
    return [1, "two", {"three": 3}]


@pytest.fixture
def conflict_data():
    """Data with structural conflicts for analyzer testing."""
    return [
        {"user": {"name": "John", "email": "john@test.com"}},
        {"user": {"name": "Jane", "email": "jane@test.com"}},
        {"product": {"id": 123, "price": 99.99}},
        {"config": {"version": "1.0", "debug": True}},
    ]


@pytest.fixture
def perfect_schema():
    """Schema that should score perfectly."""
    return {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "minLength": 1,
                "maxLength": 100,
                "pattern": "^[a-zA-Z]+$",
            },
            "age": {"type": "integer", "minimum": 0, "maximum": 150},
        },
        "additionalProperties": False,
    }


@pytest.fixture
def incomplete_schema():
    """Schema missing constraints."""
    return {
        "type": "object",
        "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
    }


@pytest.fixture
def ambiguous_schema():
    """Schema with anyOf/oneOf that increases ambiguity."""
    return {
        "type": "array",
        "items": {
            "anyOf": [
                {"type": "string"},
                {"type": "integer"},
                {"type": "object", "properties": {"x": {"type": "number"}}},
            ]
        },
    }
