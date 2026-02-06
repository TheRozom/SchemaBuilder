from typing import Any

import pytest

from src.bl.analyzer import SchemaAnalyzer
from src.bl.builder import SchemaBuilderService
from src.bl.scoring.engine.scoring_engine import ScoringEngine
from src.bl.validator import SchemaValidator


class MockAIService:
    def __init__(self, score_response: int | None = 99):
        self._score_response = score_response
        self.evaluate_schema_calls: list[dict[str, Any]] = []

    async def evaluate_schema(self, schema: dict[str, Any]) -> int | None:
        self.evaluate_schema_calls.append(schema)

        return self._score_response


class FailingAIService:
    async def evaluate_schema(self, schema: dict[str, Any]) -> int | None:
        raise Exception("AI service unavailable")


@pytest.fixture
def mock_ai_service():
    return MockAIService()


@pytest.fixture
def failing_ai_service():
    return FailingAIService()


@pytest.fixture
def schema_service():
    return SchemaBuilderService()


@pytest.fixture
def schema_service_no_ai():
    return SchemaBuilderService()


@pytest.fixture
def scoring_engine():
    return ScoringEngine()


@pytest.fixture
def schema_analyzer():
    return SchemaAnalyzer()


@pytest.fixture
def schema_validator():
    return SchemaValidator()


@pytest.fixture
def simple_object():
    return {"name": "John", "age": 30}


@pytest.fixture
def nested_object():
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
    return [
        {"name": "John", "age": 30},
        {"name": "Jane", "age": 25},
        {"name": "Bob", "age": 35},
    ]


@pytest.fixture
def mixed_array():
    return [1, "two", {"three": 3}]


@pytest.fixture
def conflict_data():
    return [
        {"user": {"name": "John", "email": "john@test.com"}},
        {"user": {"name": "Jane", "email": "jane@test.com"}},
        {"product": {"id": 123, "price": 99.99}},
        {"config": {"version": "1.0", "debug": True}},
    ]


@pytest.fixture
def perfect_schema():
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
    return {
        "type": "object",
        "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
    }


@pytest.fixture
def ambiguous_schema():
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
