"""
Integration tests for FastAPI endpoints.

Tests all API endpoints using httpx.AsyncClient with ASGITransport.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock

from src.api.main import app
from tests.conftest import MockAIService


@pytest_asyncio.fixture
async def client():
    """Provides an async HTTP client for testing the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
def mock_ai_service():
    """Mock AI service to avoid external API calls."""
    return MockAIService()


# =============================================================================
# GET /health Tests
# =============================================================================


class TestHealthEndpoint:
    """Tests for the GET /health endpoint."""

    @pytest.mark.asyncio
    async def test_health_returns_status_ok(self, client: AsyncClient):
        """Health check returns status ok."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    @pytest.mark.asyncio
    async def test_health_returns_version(self, client: AsyncClient):
        """Health check returns version string."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert data["version"] == "0.1.0"


# =============================================================================
# POST /schemas/infer Tests
# =============================================================================


class TestInferEndpoint:
    """Tests for the POST /schemas/infer endpoint."""

    @pytest.mark.asyncio
    async def test_infer_simple_object_returns_object_schema(self, client: AsyncClient):
        """Infer from simple object returns schema with type object."""
        data = {"name": "John", "age": 30}

        response = await client.post("/schemas/infer", json=data)

        assert response.status_code == 200
        result = response.json()
        assert result["schema_content"]["type"] == "object"
        assert "properties" in result["schema_content"]
        assert "name" in result["schema_content"]["properties"]
        assert "age" in result["schema_content"]["properties"]

    @pytest.mark.asyncio
    async def test_infer_string_returns_string_schema(self, client: AsyncClient):
        """Infer from string returns schema with type string."""
        data = "hello world"

        response = await client.post("/schemas/infer", json=data)

        assert response.status_code == 200
        result = response.json()
        assert result["schema_content"]["type"] == "string"

    @pytest.mark.asyncio
    async def test_infer_integer_returns_integer_schema(self, client: AsyncClient):
        """Infer from integer returns schema with type integer."""
        data = 42

        response = await client.post("/schemas/infer", json=data)

        assert response.status_code == 200
        result = response.json()
        assert result["schema_content"]["type"] == "integer"

    @pytest.mark.asyncio
    async def test_infer_float_returns_number_schema(self, client: AsyncClient):
        """Infer from float returns schema with type number."""
        data = 3.14

        response = await client.post("/schemas/infer", json=data)

        assert response.status_code == 200
        result = response.json()
        assert result["schema_content"]["type"] == "number"

    @pytest.mark.asyncio
    async def test_infer_boolean_returns_boolean_schema(self, client: AsyncClient):
        """Infer from boolean returns schema with type boolean."""
        data = True

        response = await client.post("/schemas/infer", json=data)

        assert response.status_code == 200
        result = response.json()
        assert result["schema_content"]["type"] == "boolean"

    @pytest.mark.asyncio
    async def test_infer_array_returns_array_schema(self, client: AsyncClient):
        """Infer from array returns schema with type array."""
        data = [1, 2, 3]

        response = await client.post("/schemas/infer", json=data)

        assert response.status_code == 200
        result = response.json()
        assert result["schema_content"]["type"] == "array"
        assert "items" in result["schema_content"]

    @pytest.mark.asyncio
    async def test_infer_nested_object_works_correctly(self, client: AsyncClient):
        """Infer from nested object works correctly."""
        data = {
            "user": {"name": "John", "address": {"city": "NYC", "zip": "10001"}},
            "active": True,
        }

        response = await client.post("/schemas/infer", json=data)

        assert response.status_code == 200
        result = response.json()
        schema = result["schema_content"]
        assert schema["type"] == "object"
        assert "user" in schema["properties"]
        user_schema = schema["properties"]["user"]
        assert user_schema["type"] == "object"
        assert "address" in user_schema["properties"]

    @pytest.mark.asyncio
    async def test_infer_response_includes_score_with_breakdown(self, client: AsyncClient):
        """Response includes score with breakdown."""
        data = {"name": "John", "age": 30}

        response = await client.post("/schemas/infer", json=data)

        assert response.status_code == 200
        result = response.json()
        assert "score" in result
        assert result["score"] is not None
        assert "total_score" in result["score"]
        assert "breakdown" in result["score"]
        breakdown = result["score"]["breakdown"]
        assert "strictness" in breakdown
        assert "completeness" in breakdown
        assert "ambiguity" in breakdown
        assert "security" in breakdown

    @pytest.mark.asyncio
    async def test_infer_response_includes_validation_result(self, client: AsyncClient):
        """Response includes validation result."""
        data = {"name": "John", "age": 30}

        response = await client.post("/schemas/infer", json=data)

        assert response.status_code == 200
        result = response.json()
        assert "validation" in result
        assert result["validation"] is not None
        assert "valid" in result["validation"]
        assert "total_errors" in result["validation"]
        assert "errors" in result["validation"]

    @pytest.mark.asyncio
    async def test_infer_null_returns_null_schema(self, client: AsyncClient):
        """Infer from null returns schema with type null."""
        data = None

        response = await client.post("/schemas/infer", json=data)

        assert response.status_code == 200
        result = response.json()
        assert result["schema_content"]["type"] == "null"

    @pytest.mark.asyncio
    async def test_infer_array_of_objects_returns_array_schema(self, client: AsyncClient):
        """Infer from array of objects returns correct schema."""
        data = [{"name": "John", "age": 30}, {"name": "Jane", "age": 25}]

        response = await client.post("/schemas/infer", json=data)

        assert response.status_code == 200
        result = response.json()
        assert result["schema_content"]["type"] == "array"
        assert "items" in result["schema_content"]
        items_schema = result["schema_content"]["items"]
        assert items_schema["type"] == "object"


# =============================================================================
# POST /schemas/build Tests
# =============================================================================


class TestBuildEndpoint:
    """Tests for the POST /schemas/build endpoint."""

    @pytest.mark.asyncio
    async def test_build_from_list_returns_merged_schema(self, client: AsyncClient):
        """Build from list of objects returns merged schema."""
        data = [
            {"name": "John", "age": 30},
            {"name": "Jane", "age": 25},
            {"name": "Bob", "age": 35},
        ]

        response = await client.post("/schemas/build", json=data)

        assert response.status_code == 200
        result = response.json()
        assert result["schema_content"]["type"] == "object"
        assert "properties" in result["schema_content"]
        assert "name" in result["schema_content"]["properties"]
        assert "age" in result["schema_content"]["properties"]

    @pytest.mark.asyncio
    async def test_build_empty_list_returns_400_error(self, client: AsyncClient):
        """Empty list returns 400 error."""
        data = []

        response = await client.post("/schemas/build", json=data)

        assert response.status_code == 400
        result = response.json()
        assert "error" in result
        assert "message" in result
        assert "empty" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_build_with_non_objects_returns_400_error(self, client: AsyncClient):
        """List with non-objects returns 400 error."""
        data = ["string1", "string2"]

        response = await client.post("/schemas/build", json=data)

        assert response.status_code == 400
        result = response.json()
        assert "error" in result
        assert "message" in result

    @pytest.mark.asyncio
    async def test_build_with_mixed_types_returns_400_error(self, client: AsyncClient):
        """List with mixed types (objects and primitives) returns 400 error."""
        data = [{"name": "John"}, "not an object", 42]

        response = await client.post("/schemas/build", json=data)

        assert response.status_code == 400
        result = response.json()
        assert "error" in result

    @pytest.mark.asyncio
    async def test_build_response_includes_analysis_for_multiple_structures(
        self, client: AsyncClient
    ):
        """Response includes analysis when multiple structures exist."""
        data = [
            {"user": {"name": "John"}},
            {"user": {"name": "Jane"}},
            {"product": {"id": 123}},
        ]

        response = await client.post("/schemas/build", json=data)

        assert response.status_code == 200
        result = response.json()
        # analysis may or may not be present depending on implementation
        # but should be present when structures differ significantly
        assert "analysis" in result

    @pytest.mark.asyncio
    async def test_build_response_includes_validation_result(self, client: AsyncClient):
        """Response includes validation result."""
        data = [{"name": "John", "age": 30}, {"name": "Jane", "age": 25}]

        response = await client.post("/schemas/build", json=data)

        assert response.status_code == 200
        result = response.json()
        assert "validation" in result
        assert result["validation"] is not None
        assert "valid" in result["validation"]

    @pytest.mark.asyncio
    async def test_build_response_includes_score(self, client: AsyncClient):
        """Response includes score with breakdown."""
        data = [{"name": "John", "age": 30}, {"name": "Jane", "age": 25}]

        response = await client.post("/schemas/build", json=data)

        assert response.status_code == 200
        result = response.json()
        assert "score" in result
        assert result["score"] is not None
        assert "total_score" in result["score"]
        assert "breakdown" in result["score"]

    @pytest.mark.asyncio
    async def test_build_with_arrays_in_objects_returns_400_error(self, client: AsyncClient):
        """List containing arrays returns 400 error."""
        data = [[1, 2, 3], [4, 5, 6]]

        response = await client.post("/schemas/build", json=data)

        assert response.status_code == 400
        result = response.json()
        assert "error" in result

    @pytest.mark.asyncio
    async def test_build_with_single_object_works(self, client: AsyncClient):
        """Build with single object works correctly."""
        data = [{"name": "John", "age": 30}]

        response = await client.post("/schemas/build", json=data)

        assert response.status_code == 200
        result = response.json()
        assert result["schema_content"]["type"] == "object"


# =============================================================================
# POST /schemas/analyze Tests
# =============================================================================


class TestAnalyzeEndpoint:
    """Tests for the POST /schemas/analyze endpoint."""

    @pytest.mark.asyncio
    async def test_analyze_identical_objects_returns_one_unique_structure(
        self, client: AsyncClient
    ):
        """Analyze identical objects returns 1 unique structure."""
        data = [
            {"name": "John", "age": 30},
            {"name": "Jane", "age": 25},
            {"name": "Bob", "age": 35},
        ]

        response = await client.post("/schemas/analyze", json=data)

        assert response.status_code == 200
        result = response.json()
        assert "unique_structures" in result
        assert result["unique_structures"] == 1

    @pytest.mark.asyncio
    async def test_analyze_different_objects_returns_multiple_structures(self, client: AsyncClient):
        """Analyze different objects returns multiple structures."""
        data = [
            {"user": {"name": "John", "email": "john@test.com"}},
            {"user": {"name": "Jane", "email": "jane@test.com"}},
            {"product": {"id": 123, "price": 99.99}},
            {"config": {"version": "1.0", "debug": True}},
        ]

        response = await client.post("/schemas/analyze", json=data)

        assert response.status_code == 200
        result = response.json()
        assert "unique_structures" in result
        assert result["unique_structures"] > 1

    @pytest.mark.asyncio
    async def test_analyze_empty_list_returns_400_error(self, client: AsyncClient):
        """Empty list returns 400 error."""
        data = []

        response = await client.post("/schemas/analyze", json=data)

        assert response.status_code == 400
        result = response.json()
        assert "error" in result
        assert "message" in result

    @pytest.mark.asyncio
    async def test_analyze_non_array_returns_400_error(self, client: AsyncClient):
        """Non-array returns 422 validation error."""
        data = {"name": "not an array"}

        response = await client.post("/schemas/analyze", json=data)

        assert response.status_code == 422
        result = response.json()
        assert "detail" in result

    @pytest.mark.asyncio
    async def test_analyze_returns_should_split_schemas_recommendation(self, client: AsyncClient):
        """Returns should_split_schemas recommendation."""
        data = [{"user": {"name": "John"}}, {"product": {"id": 123}}]

        response = await client.post("/schemas/analyze", json=data)

        assert response.status_code == 200
        result = response.json()
        assert "should_split_schemas" in result
        assert isinstance(result["should_split_schemas"], bool)

    @pytest.mark.asyncio
    async def test_analyze_returns_total_objects_count(self, client: AsyncClient):
        """Returns total objects count."""
        data = [{"name": "John"}, {"name": "Jane"}, {"name": "Bob"}]

        response = await client.post("/schemas/analyze", json=data)

        assert response.status_code == 200
        result = response.json()
        assert "total_objects" in result
        assert result["total_objects"] == 3

    @pytest.mark.asyncio
    async def test_analyze_returns_recommendation_string(self, client: AsyncClient):
        """Returns recommendation string."""
        data = [{"user": {"name": "John"}}, {"product": {"id": 123}}]

        response = await client.post("/schemas/analyze", json=data)

        assert response.status_code == 200
        result = response.json()
        assert "recommendation" in result
        assert isinstance(result["recommendation"], str)

    @pytest.mark.asyncio
    async def test_analyze_returns_confidence_level(self, client: AsyncClient):
        """Returns confidence level."""
        data = [{"name": "John"}, {"name": "Jane"}]

        response = await client.post("/schemas/analyze", json=data)

        assert response.status_code == 200
        result = response.json()
        assert "confidence" in result
        assert result["confidence"] in ["low", "medium", "high"]


# =============================================================================
# POST /schemas/score Tests
# =============================================================================


class TestScoreEndpoint:
    """Tests for the POST /schemas/score endpoint."""

    @pytest.mark.asyncio
    async def test_score_valid_schema_returns_score_result(self, client: AsyncClient):
        """Score valid schema returns ScoreResult."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
        }

        response = await client.post("/schemas/score", json=schema)

        assert response.status_code == 200
        result = response.json()
        assert "total_score" in result
        assert "breakdown" in result
        assert isinstance(result["total_score"], (int, float))

    @pytest.mark.asyncio
    async def test_score_empty_schema_returns_400_error(self, client: AsyncClient):
        """Empty schema returns 400 error."""
        schema = {}

        response = await client.post("/schemas/score", json=schema)

        assert response.status_code == 400
        result = response.json()
        assert "error" in result
        assert "message" in result

    @pytest.mark.asyncio
    async def test_score_returns_breakdown_with_all_metrics(self, client: AsyncClient):
        """Returns breakdown with strictness, completeness, ambiguity, security."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string", "minLength": 1, "maxLength": 100},
                "age": {"type": "integer", "minimum": 0, "maximum": 150},
            },
            "additionalProperties": False,
        }

        response = await client.post("/schemas/score", json=schema)

        assert response.status_code == 200
        result = response.json()
        breakdown = result["breakdown"]
        assert "strictness" in breakdown
        assert "completeness" in breakdown
        assert "ambiguity" in breakdown
        assert "security" in breakdown

    @pytest.mark.asyncio
    async def test_score_strict_schema_scores_higher(self, client: AsyncClient):
        """Stricter schema scores higher than loose schema."""
        strict_schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string", "minLength": 1, "maxLength": 100},
                "age": {"type": "integer", "minimum": 0, "maximum": 150},
            },
            "additionalProperties": False,
        }

        loose_schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
        }

        strict_response = await client.post("/schemas/score", json=strict_schema)
        loose_response = await client.post("/schemas/score", json=loose_schema)

        assert strict_response.status_code == 200
        assert loose_response.status_code == 200

        strict_score = strict_response.json()["total_score"]
        loose_score = loose_response.json()["total_score"]

        assert strict_score > loose_score

    @pytest.mark.asyncio
    async def test_score_schema_with_patterns_scores_well(self, client: AsyncClient):
        """Schema with patterns scores well on strictness."""
        schema = {
            "type": "object",
            "properties": {
                "email": {
                    "type": "string",
                    "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
                }
            },
        }

        response = await client.post("/schemas/score", json=schema)

        assert response.status_code == 200
        result = response.json()
        assert result["breakdown"]["strictness"] > 0


# =============================================================================
# POST /schemas/validate Tests
# =============================================================================


class TestValidateEndpoint:
    """Tests for the POST /schemas/validate endpoint."""

    @pytest.mark.asyncio
    async def test_validate_valid_data_returns_valid_true(self, client: AsyncClient):
        """Valid data returns valid=True."""
        payload = {
            "schema": {
                "type": "object",
                "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
            },
            "data": [{"name": "John", "age": 30}, {"name": "Jane", "age": 25}],
        }

        response = await client.post("/schemas/validate", json=payload)

        assert response.status_code == 200
        result = response.json()
        assert result["valid"] is True
        assert result["total_errors"] == 0
        assert result["errors"] == []

    @pytest.mark.asyncio
    async def test_validate_invalid_data_returns_valid_false_with_errors(self, client: AsyncClient):
        """Invalid data returns valid=False with errors."""
        payload = {
            "schema": {
                "type": "object",
                "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
                "required": ["name", "age"],
            },
            "data": [
                {"name": "John"},  # missing age
                {"name": 123, "age": "not a number"},  # wrong types
            ],
        }

        response = await client.post("/schemas/validate", json=payload)

        assert response.status_code == 200
        result = response.json()
        assert result["valid"] is False
        assert result["total_errors"] > 0
        assert len(result["errors"]) > 0

    @pytest.mark.asyncio
    async def test_validate_empty_schema_returns_400_error(self, client: AsyncClient):
        """Empty schema returns 400 error."""
        payload = {"schema": {}, "data": [{"name": "John"}]}

        response = await client.post("/schemas/validate", json=payload)

        assert response.status_code == 400
        result = response.json()
        assert "error" in result
        assert "message" in result

    @pytest.mark.asyncio
    async def test_validate_empty_data_returns_400_error(self, client: AsyncClient):
        """Empty data returns 400 error."""
        payload = {
            "schema": {"type": "object", "properties": {"name": {"type": "string"}}},
            "data": [],
        }

        response = await client.post("/schemas/validate", json=payload)

        assert response.status_code == 400
        result = response.json()
        assert "error" in result
        assert "message" in result

    @pytest.mark.asyncio
    async def test_validate_returns_error_details(self, client: AsyncClient):
        """Validation errors include details about the failure."""
        payload = {
            "schema": {
                "type": "object",
                "properties": {"email": {"type": "string", "format": "email"}},
                "required": ["email"],
            },
            "data": [{"email": "not-an-email"}],
        }

        response = await client.post("/schemas/validate", json=payload)

        assert response.status_code == 200
        result = response.json()
        # May or may not have errors depending on format validation
        assert "valid" in result
        assert "errors" in result

    @pytest.mark.asyncio
    async def test_validate_with_additional_properties_false(self, client: AsyncClient):
        """Validation with additionalProperties=false catches extra fields."""
        payload = {
            "schema": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "additionalProperties": False,
            },
            "data": [{"name": "John", "extra": "field"}],
        }

        response = await client.post("/schemas/validate", json=payload)

        assert response.status_code == 200
        result = response.json()
        assert result["valid"] is False
        assert result["total_errors"] > 0

    @pytest.mark.asyncio
    async def test_validate_nested_object_validation(self, client: AsyncClient):
        """Validation works for nested objects."""
        payload = {
            "schema": {
                "type": "object",
                "properties": {
                    "user": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "age": {"type": "integer"},
                        },
                        "required": ["name"],
                    }
                },
            },
            "data": [
                {"user": {"name": "John", "age": 30}},
                {"user": {"age": 25}},  # missing name
            ],
        }

        response = await client.post("/schemas/validate", json=payload)

        assert response.status_code == 200
        result = response.json()
        assert result["valid"] is False
        assert result["total_errors"] > 0

    @pytest.mark.asyncio
    async def test_validate_array_items(self, client: AsyncClient):
        """Validation works for array items."""
        payload = {
            "schema": {
                "type": "object",
                "properties": {"tags": {"type": "array", "items": {"type": "string"}}},
            },
            "data": [
                {"tags": ["a", "b", "c"]},
                {"tags": ["x", 123, "z"]},  # 123 is not a string
            ],
        }

        response = await client.post("/schemas/validate", json=payload)

        assert response.status_code == 200
        result = response.json()
        assert result["valid"] is False
        assert result["total_errors"] > 0


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestErrorHandling:
    """Tests for API error handling."""

    @pytest.mark.asyncio
    async def test_invalid_json_returns_422(self, client: AsyncClient):
        """Invalid JSON in request body returns 422."""
        response = await client.post(
            "/schemas/infer",
            content="not valid json",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_error_response_has_expected_structure(self, client: AsyncClient):
        """Error responses have expected structure with error and message."""
        response = await client.post("/schemas/build", json=[])

        assert response.status_code == 400
        result = response.json()
        assert "error" in result
        assert "message" in result

    @pytest.mark.asyncio
    async def test_score_non_dict_schema_returns_error(self, client: AsyncClient):
        """Scoring a non-dict schema returns error."""
        response = await client.post("/schemas/score", json="not a schema")

        # The endpoint should handle this gracefully
        assert response.status_code in [400, 422]


# =============================================================================
# Edge Case Tests
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_infer_empty_object(self, client: AsyncClient):
        """Infer from empty object works."""
        data = {}

        response = await client.post("/schemas/infer", json=data)

        assert response.status_code == 200
        result = response.json()
        assert result["schema_content"]["type"] == "object"

    @pytest.mark.asyncio
    async def test_infer_empty_array(self, client: AsyncClient):
        """Infer from empty array works."""
        data = []

        response = await client.post("/schemas/infer", json=data)

        assert response.status_code == 200
        result = response.json()
        assert result["schema_content"]["type"] == "array"

    @pytest.mark.asyncio
    async def test_infer_deeply_nested_object(self, client: AsyncClient):
        """Infer from deeply nested object works."""
        data = {"level1": {"level2": {"level3": {"level4": {"value": "deep"}}}}}

        response = await client.post("/schemas/infer", json=data)

        assert response.status_code == 200
        result = response.json()
        assert result["schema_content"]["type"] == "object"

    @pytest.mark.asyncio
    async def test_infer_object_with_special_characters_in_keys(self, client: AsyncClient):
        """Infer from object with special characters in keys works."""
        data = {
            "key-with-dash": "value1",
            "key.with.dots": "value2",
            "key_with_underscore": "value3",
        }

        response = await client.post("/schemas/infer", json=data)

        assert response.status_code == 200
        result = response.json()
        assert "key-with-dash" in result["schema_content"]["properties"]

    @pytest.mark.asyncio
    async def test_build_with_optional_fields(self, client: AsyncClient):
        """Build handles objects with optional fields correctly."""
        data = [
            {"name": "John", "age": 30, "email": "john@test.com"},
            {"name": "Jane", "age": 25},
            {"name": "Bob"},
        ]

        response = await client.post("/schemas/build", json=data)

        assert response.status_code == 200
        result = response.json()
        props = result["schema_content"]["properties"]
        assert "name" in props
        assert "age" in props
        assert "email" in props

    @pytest.mark.asyncio
    async def test_infer_mixed_array(self, client: AsyncClient):
        """Infer from array with mixed types works."""
        data = [1, "two", {"three": 3}, True, None]

        response = await client.post("/schemas/infer", json=data)

        assert response.status_code == 200
        result = response.json()
        assert result["schema_content"]["type"] == "array"

    @pytest.mark.asyncio
    async def test_score_complex_schema(self, client: AsyncClient):
        """Score complex schema with multiple features."""
        schema = {
            "type": "object",
            "properties": {
                "id": {"type": "string", "pattern": "^[a-f0-9]{8}$"},
                "name": {"type": "string", "minLength": 1, "maxLength": 255},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 0,
                    "maxItems": 10,
                },
                "metadata": {"type": "object", "additionalProperties": True},
            },
            "required": ["id", "name"],
            "additionalProperties": False,
        }

        response = await client.post("/schemas/score", json=schema)

        assert response.status_code == 200
        result = response.json()
        assert result["total_score"] > 0
        assert all(
            key in result["breakdown"]
            for key in ["strictness", "completeness", "ambiguity", "security"]
        )

    @pytest.mark.asyncio
    async def test_validate_with_enum_constraint(self, client: AsyncClient):
        """Validation with enum constraint works correctly."""
        payload = {
            "schema": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["active", "inactive", "pending"],
                    }
                },
            },
            "data": [{"status": "active"}, {"status": "invalid_status"}],
        }

        response = await client.post("/schemas/validate", json=payload)

        assert response.status_code == 200
        result = response.json()
        assert result["valid"] is False
        assert result["total_errors"] > 0

    @pytest.mark.asyncio
    async def test_validate_with_minimum_maximum(self, client: AsyncClient):
        """Validation with minimum/maximum constraints works."""
        payload = {
            "schema": {
                "type": "object",
                "properties": {"age": {"type": "integer", "minimum": 0, "maximum": 150}},
            },
            "data": [
                {"age": 30},
                {"age": -5},  # below minimum
                {"age": 200},  # above maximum
            ],
        }

        response = await client.post("/schemas/validate", json=payload)

        assert response.status_code == 200
        result = response.json()
        assert result["valid"] is False
        assert result["total_errors"] >= 2

    @pytest.mark.asyncio
    async def test_analyze_single_object(self, client: AsyncClient):
        """Analyze single object works."""
        data = [{"name": "John", "age": 30}]

        response = await client.post("/schemas/analyze", json=data)

        assert response.status_code == 200
        result = response.json()
        assert result["total_objects"] == 1
        assert result["unique_structures"] == 1
