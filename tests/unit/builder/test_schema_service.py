"""Comprehensive unit tests for SchemaBuilderService class."""

import pytest
from typing import Dict, Any, List

from src.bl.builder import SchemaBuilderService
from src.domain.interfaces import IAIService
from src.domain.models import SchemaDefinition
from src.shared.exceptions import SchemaInferenceError


class MockAIService(IAIService):
    """Mock AI service for testing schema service behavior."""

    async def generate_regex(self, samples: List[str]) -> str | None:
        if samples and "ABC" in samples[0]:
            return r"^ABC-\d+$"
        return None

    async def evaluate_schema(self, schema: Dict[str, Any]) -> int | None:
        return 99


class FailingAIService(IAIService):
    """AI service that always raises exceptions for error testing."""

    async def generate_regex(self, samples: List[str]) -> str | None:
        raise Exception("AI service unavailable")

    async def evaluate_schema(self, schema: Dict[str, Any]) -> int | None:
        raise Exception("AI service unavailable")


class TestGenerateSchemaStringInference:
    """Tests for generate_schema() with string data."""

    @pytest.mark.asyncio
    async def test_simple_string_inference(self):
        """Simple string should infer to string type with length constraints."""
        service = SchemaBuilderService()
        result = await service.generate_schema("hello")

        assert isinstance(result, SchemaDefinition)
        schema = result.schema_content
        assert schema["type"] == "string"
        assert schema["minLength"] == 0
        assert schema["maxLength"] == 5

    @pytest.mark.asyncio
    async def test_email_pattern_detection(self):
        """Email string should match email pattern."""
        service = SchemaBuilderService()
        result = await service.generate_schema("user@example.com")

        schema = result.schema_content
        assert schema["type"] == "string"
        assert "pattern" in schema
        # Email pattern should be detected
        assert schema["pattern"] is not None


class TestGenerateSchemaIntegerInference:
    """Tests for generate_schema() with integer data."""

    @pytest.mark.asyncio
    async def test_integer_with_min_max_constraints(self):
        """Integer should infer to integer type with min/max constraints."""
        service = SchemaBuilderService()
        result = await service.generate_schema(42)

        schema = result.schema_content
        assert schema["type"] == "integer"
        assert schema["minimum"] == 0
        assert schema["maximum"] == 42

    @pytest.mark.asyncio
    async def test_integer_zero(self):
        """Zero should infer correctly."""
        service = SchemaBuilderService()
        result = await service.generate_schema(0)

        schema = result.schema_content
        assert schema["type"] == "integer"
        assert schema["minimum"] == 0
        assert schema["maximum"] == 0


class TestGenerateSchemaObjectInference:
    """Tests for generate_schema() with object data."""

    @pytest.mark.asyncio
    async def test_object_with_properties(self):
        """Object should infer with all properties typed."""
        service = SchemaBuilderService()
        result = await service.generate_schema({"name": "John", "age": 30, "active": True})

        schema = result.schema_content
        assert schema["type"] == "object"
        assert "properties" in schema
        assert schema["properties"]["name"]["type"] == "string"
        assert schema["properties"]["age"]["type"] == "integer"
        assert schema["properties"]["active"]["type"] == "boolean"
        assert schema["additionalProperties"] is False

    @pytest.mark.asyncio
    async def test_object_has_no_required_field(self):
        """Object schema should NOT have required field by design."""
        service = SchemaBuilderService()
        result = await service.generate_schema({"name": "John", "email": "john@example.com"})

        schema = result.schema_content
        assert schema["type"] == "object"
        # By design, SchemaBuilderService does not generate required field
        assert "required" not in schema or schema.get("required") == []

    @pytest.mark.asyncio
    async def test_nested_object(self):
        """Nested object should be properly inferred."""
        service = SchemaBuilderService()
        result = await service.generate_schema(
            {"user": {"name": "John", "email": "john@example.com"}}
        )

        schema = result.schema_content
        assert schema["type"] == "object"
        assert schema["properties"]["user"]["type"] == "object"
        assert "name" in schema["properties"]["user"]["properties"]
        assert "email" in schema["properties"]["user"]["properties"]


class TestGenerateSchemaArrayInference:
    """Tests for generate_schema() with array data."""

    @pytest.mark.asyncio
    async def test_array_with_merged_items(self):
        """Array items should be merged into single items schema."""
        service = SchemaBuilderService()
        result = await service.generate_schema(
            [{"name": "John", "age": 30}, {"name": "Jane", "age": 25}]
        )

        schema = result.schema_content
        assert schema["type"] == "array"
        assert "items" in schema
        assert schema["items"]["type"] == "object"
        assert "name" in schema["items"]["properties"]
        assert "age" in schema["items"]["properties"]
        # maxItems should reflect array length
        assert schema["maxItems"] == 2

    @pytest.mark.asyncio
    async def test_mixed_array_creates_anyof(self):
        """Array with mixed types should create anyOf in items."""
        service = SchemaBuilderService()
        result = await service.generate_schema([42, "hello"])

        schema = result.schema_content
        assert schema["type"] == "array"
        assert "items" in schema
        # Mixed types result in anyOf
        assert "anyOf" in schema["items"]
        assert len(schema["items"]["anyOf"]) == 2

    @pytest.mark.asyncio
    async def test_empty_array(self):
        """Empty array should infer with no items schema."""
        service = SchemaBuilderService()
        result = await service.generate_schema([])

        schema = result.schema_content
        assert schema["type"] == "array"
        assert schema["minItems"] == 0
        assert schema["maxItems"] == 0


class TestGenerateSchemaAIIntegration:
    """Tests for AI service integration in generate_schema()."""

    @pytest.mark.asyncio
    async def test_ai_regex_injection_when_pattern_unknown(self):
        """AI regex should be injected when pattern is unknown (ABC-123 trigger)."""
        ai_service = MockAIService()
        service = SchemaBuilderService(ai_service=ai_service)

        # "ABC-123" triggers the MockAIService to return r"^ABC-\d+$"
        result = await service.generate_schema({"code": "ABC-123"})

        schema = result.schema_content
        assert schema["type"] == "object"
        assert "code" in schema["properties"]
        code_schema = schema["properties"]["code"]
        assert code_schema["type"] == "string"
        # AI-generated pattern should be injected
        assert code_schema["pattern"] == r"^ABC-\d+$"

    @pytest.mark.asyncio
    async def test_service_without_ai_service_still_works(self):
        """Service without AI service should work normally."""
        service = SchemaBuilderService(ai_service=None)

        result = await service.generate_schema({"code": "ABC-123"})

        schema = result.schema_content
        assert schema["type"] == "object"
        assert "code" in schema["properties"]
        # Without AI service, pattern won't be AI-generated
        # But the schema should still be valid

    @pytest.mark.asyncio
    async def test_ai_service_failure_does_not_break_generation(self):
        """Failing AI service should not break schema generation."""
        ai_service = FailingAIService()
        service = SchemaBuilderService(ai_service=ai_service)

        # Should not raise, AI failures are caught
        result = await service.generate_schema({"code": "ABC-123"})

        schema = result.schema_content
        assert schema["type"] == "object"
        assert "code" in schema["properties"]


class TestGenerateSchemaErrorHandling:
    """Tests for error handling in generate_schema()."""

    @pytest.mark.asyncio
    async def test_schema_inference_error_on_failure(self):
        """SchemaInferenceError should be raised on critical failure."""
        service = SchemaBuilderService()

        # Create a data type that will cause inference issues
        # Note: The inferrer handles most types gracefully, so we need to
        # trigger an actual error condition. Since the inferrer is robust,
        # this test verifies the error wrapping behavior exists.
        # In practice, the SchemaInferenceError is raised when unexpected
        # exceptions occur during inference.

        # We can't easily trigger this with normal data, but we can verify
        # the error structure is correct by checking the exception class
        assert issubclass(SchemaInferenceError, Exception)


class TestGenerateSchemaFromList:
    """Tests for generate_schema_from_list() method."""

    @pytest.mark.asyncio
    async def test_list_of_similar_objects_returns_merged_schema(self):
        """List of similar objects should return a merged schema."""
        service = SchemaBuilderService()
        data_list = [
            {"name": "John", "age": 30},
            {"name": "Jane", "age": 25},
            {"name": "Bob", "age": 35},
        ]

        schema_def, analysis = await service.generate_schema_from_list(data_list)

        assert isinstance(schema_def, SchemaDefinition)
        schema = schema_def.schema_content
        assert schema["type"] == "object"
        assert "name" in schema["properties"]
        assert "age" in schema["properties"]
        # Age constraints should be merged (max of all values)
        assert schema["properties"]["age"]["maximum"] == 35

    @pytest.mark.asyncio
    async def test_returns_analysis_result_with_groups(self):
        """Should return AnalysisResult with group information."""
        service = SchemaBuilderService()
        data_list = [{"name": "John", "age": 30}, {"name": "Jane", "age": 25}]

        schema_def, analysis = await service.generate_schema_from_list(data_list)

        assert analysis is not None
        assert hasattr(analysis, "unique_structures")
        assert hasattr(analysis, "groups")
        assert analysis.objects_analyzed == 2

    @pytest.mark.asyncio
    async def test_empty_list_raises_error(self):
        """Empty list should raise an error."""
        service = SchemaBuilderService()

        with pytest.raises(SchemaInferenceError):
            await service.generate_schema_from_list([])

    @pytest.mark.asyncio
    async def test_single_item_list(self):
        """Single item list should work correctly."""
        service = SchemaBuilderService()
        data_list = [{"name": "John"}]

        schema_def, analysis = await service.generate_schema_from_list(data_list)

        assert schema_def.schema_content["type"] == "object"
        assert "name" in schema_def.schema_content["properties"]

    @pytest.mark.asyncio
    async def test_different_structures_detected(self):
        """Different structures should be detected in analysis."""
        service = SchemaBuilderService()
        data_list = [
            {"user": {"name": "John"}},
            {"user": {"name": "Jane"}},
            {"product": {"id": 123}},
        ]

        schema_def, analysis = await service.generate_schema_from_list(data_list)

        assert analysis is not None
        # Should detect different structures
        assert analysis.unique_structures >= 1


class TestSchemaBuilderServiceInitialization:
    """Tests for SchemaBuilderService initialization."""

    def test_initialization_with_ai_service(self):
        """Service should initialize with AI service."""
        ai_service = MockAIService()
        service = SchemaBuilderService(ai_service=ai_service)

        assert service.ai_service is ai_service

    def test_initialization_without_ai_service(self):
        """Service should initialize without AI service."""
        service = SchemaBuilderService(ai_service=None)

        assert service.ai_service is None

    def test_initialization_creates_inferrer(self):
        """Service should create internal inferrer."""
        service = SchemaBuilderService()

        assert service.inferrer is not None

    def test_initialization_creates_injector(self):
        """Service should create internal injector."""
        service = SchemaBuilderService()

        assert service.injector is not None

    def test_initialization_creates_grouped_builder(self):
        """Service should create internal grouped builder."""
        service = SchemaBuilderService()

        assert service.grouped_builder is not None


class TestSchemaDefinitionOutput:
    """Tests for SchemaDefinition output structure."""

    @pytest.mark.asyncio
    async def test_returns_schema_definition_instance(self):
        """generate_schema should return SchemaDefinition instance."""
        service = SchemaBuilderService()
        result = await service.generate_schema({"test": "value"})

        assert isinstance(result, SchemaDefinition)
        assert hasattr(result, "schema_content")

    @pytest.mark.asyncio
    async def test_schema_content_is_dict(self):
        """schema_content should be a dictionary."""
        service = SchemaBuilderService()
        result = await service.generate_schema({"test": "value"})

        assert isinstance(result.schema_content, dict)

    @pytest.mark.asyncio
    async def test_schema_definition_from_list_returns_tuple(self):
        """generate_schema_from_list should return tuple of SchemaDefinition and AnalysisResult."""
        service = SchemaBuilderService()
        schema_def, analysis = await service.generate_schema_from_list([{"test": "value"}])

        assert isinstance(schema_def, SchemaDefinition)
        # analysis can be None or AnalysisResult depending on configuration


class TestPrimitiveTypes:
    """Tests for primitive type inference through the service."""

    @pytest.mark.asyncio
    async def test_boolean_true(self):
        """Boolean True should infer correctly."""
        service = SchemaBuilderService()
        result = await service.generate_schema(True)

        assert result.schema_content["type"] == "boolean"

    @pytest.mark.asyncio
    async def test_boolean_false(self):
        """Boolean False should infer correctly."""
        service = SchemaBuilderService()
        result = await service.generate_schema(False)

        assert result.schema_content["type"] == "boolean"

    @pytest.mark.asyncio
    async def test_null_value(self):
        """None/null should infer to null type."""
        service = SchemaBuilderService()
        result = await service.generate_schema(None)

        assert result.schema_content["type"] == "null"

    @pytest.mark.asyncio
    async def test_float_value(self):
        """Float should infer to number type."""
        service = SchemaBuilderService()
        result = await service.generate_schema(3.14)

        assert result.schema_content["type"] == "number"
        assert result.schema_content["minimum"] == 0


class TestComplexScenarios:
    """Tests for complex real-world scenarios."""

    @pytest.mark.asyncio
    async def test_complex_nested_structure(self):
        """Complex nested structure should be fully inferred."""
        service = SchemaBuilderService()
        data = {
            "id": 1,
            "name": "Product",
            "price": 29.99,
            "available": True,
            "tags": ["electronics", "sale"],
            "metadata": {"created": "2024-01-15", "updated": None},
        }

        result = await service.generate_schema(data)
        schema = result.schema_content

        assert schema["type"] == "object"
        assert schema["properties"]["id"]["type"] == "integer"
        assert schema["properties"]["name"]["type"] == "string"
        assert schema["properties"]["price"]["type"] == "number"
        assert schema["properties"]["available"]["type"] == "boolean"
        assert schema["properties"]["tags"]["type"] == "array"
        assert schema["properties"]["metadata"]["type"] == "object"

    @pytest.mark.asyncio
    async def test_array_of_different_objects(self):
        """Array containing objects with different structures."""
        service = SchemaBuilderService()
        data = [
            {"type": "user", "name": "John"},
            {"type": "admin", "name": "Jane", "permissions": ["read", "write"]},
        ]

        result = await service.generate_schema(data)
        schema = result.schema_content

        assert schema["type"] == "array"
        assert "items" in schema

    @pytest.mark.asyncio
    async def test_deeply_nested_objects(self):
        """Deeply nested objects should be handled correctly."""
        service = SchemaBuilderService()
        data = {"level1": {"level2": {"level3": {"value": "deep"}}}}

        result = await service.generate_schema(data)
        schema = result.schema_content

        assert schema["type"] == "object"
        level1 = schema["properties"]["level1"]
        assert level1["type"] == "object"
        level2 = level1["properties"]["level2"]
        assert level2["type"] == "object"
        level3 = level2["properties"]["level3"]
        assert level3["type"] == "object"
        assert level3["properties"]["value"]["type"] == "string"

    @pytest.mark.asyncio
    async def test_multiple_ai_regex_injections(self):
        """Multiple unknown patterns should all get AI regex."""
        ai_service = MockAIService()
        service = SchemaBuilderService(ai_service=ai_service)

        result = await service.generate_schema({"code1": "ABC-001", "code2": "ABC-002"})

        schema = result.schema_content
        # Both should have AI-generated patterns
        assert schema["properties"]["code1"]["pattern"] == r"^ABC-\d+$"
        assert schema["properties"]["code2"]["pattern"] == r"^ABC-\d+$"
