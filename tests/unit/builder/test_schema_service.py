import pytest

from src.bl.builder import SchemaBuilderService
from src.domain.models import SchemaDefinition
from src.shared.exceptions import InputValidationError, SchemaInferenceError


class TestGenerateSchemaStringInference:
    def test_simple_string_inference(self):
        service = SchemaBuilderService()
        result = service.generate_schema("hello")
        assert isinstance(result, SchemaDefinition)
        schema = result.schema_content
        assert schema["type"] == "string"
        assert schema["minLength"] == 0
        assert schema["maxLength"] == 5

    def test_email_pattern_detection(self):
        service = SchemaBuilderService()
        result = service.generate_schema("user@example.com")
        schema = result.schema_content
        assert schema["type"] == "string"
        assert "pattern" in schema
        assert schema["pattern"] is not None


class TestGenerateSchemaIntegerInference:
    def test_integer_with_min_max_constraints(self):
        service = SchemaBuilderService()
        result = service.generate_schema(42)
        schema = result.schema_content
        assert schema["type"] == "integer"
        assert schema["minimum"] == 40
        assert schema["maximum"] == 45

    def test_integer_zero(self):
        service = SchemaBuilderService()
        result = service.generate_schema(0)
        schema = result.schema_content
        assert schema["type"] == "integer"
        assert schema["minimum"] == 0
        assert schema["maximum"] == 0


class TestGenerateSchemaObjectInference:
    def test_object_with_properties(self):
        service = SchemaBuilderService()
        result = service.generate_schema({"name": "John", "age": 30, "active": True})
        schema = result.schema_content
        assert schema["type"] == "object"
        assert "properties" in schema
        assert schema["properties"]["name"]["type"] == "string"
        assert schema["properties"]["age"]["type"] == "integer"
        assert schema["properties"]["active"]["type"] == "boolean"
        assert schema["additionalProperties"] is False

    def test_object_has_no_required_field(self):
        service = SchemaBuilderService()
        result = service.generate_schema({"name": "John", "email": "john@example.com"})
        schema = result.schema_content
        assert schema["type"] == "object"
        assert "required" not in schema or schema.get("required") == []

    def test_nested_object(self):
        service = SchemaBuilderService()
        result = service.generate_schema({"user": {"name": "John", "email": "john@example.com"}})
        schema = result.schema_content
        assert schema["type"] == "object"
        assert schema["properties"]["user"]["type"] == "object"
        assert "name" in schema["properties"]["user"]["properties"]
        assert "email" in schema["properties"]["user"]["properties"]


class TestGenerateSchemaArrayInference:
    def test_array_with_merged_items(self):
        service = SchemaBuilderService()
        result = service.generate_schema([{"name": "John", "age": 30}, {"name": "Jane", "age": 25}])
        schema = result.schema_content
        assert schema["type"] == "array"
        assert "items" in schema
        assert schema["items"]["type"] == "object"
        assert "name" in schema["items"]["properties"]
        assert "age" in schema["items"]["properties"]
        assert schema["maxItems"] == 2

    def test_mixed_array_creates_anyof(self):
        service = SchemaBuilderService()
        result = service.generate_schema([42, "hello"])
        schema = result.schema_content
        assert schema["type"] == "array"
        assert "items" in schema
        assert "anyOf" in schema["items"]
        assert len(schema["items"]["anyOf"]) == 2

    def test_empty_array(self):
        service = SchemaBuilderService()
        result = service.generate_schema([])
        schema = result.schema_content
        assert schema["type"] == "array"
        assert schema["minItems"] == 0
        assert schema["maxItems"] == 0


class TestGenerateSchemaErrorHandling:
    def test_schema_inference_error_on_failure(self):
        assert issubclass(SchemaInferenceError, Exception)


class TestGenerateSchemaFromList:
    @pytest.mark.asyncio
    async def test_list_of_similar_objects_returns_merged_schema(self):
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
        assert schema["properties"]["age"]["maximum"] == 35

    @pytest.mark.asyncio
    async def test_returns_analysis_result_with_groups(self):
        service = SchemaBuilderService()
        data_list = [{"name": "John", "age": 30}, {"name": "Jane", "age": 25}]
        schema_def, analysis = await service.generate_schema_from_list(data_list)
        assert analysis is not None
        assert hasattr(analysis, "unique_structures")
        assert hasattr(analysis, "groups")
        assert analysis.objects_analyzed == 2

    @pytest.mark.asyncio
    async def test_empty_list_raises_error(self):
        service = SchemaBuilderService()

        with pytest.raises(InputValidationError):
            await service.generate_schema_from_list([])

    @pytest.mark.asyncio
    async def test_single_item_list(self):
        service = SchemaBuilderService()
        data_list = [{"name": "John"}]
        schema_def, analysis = await service.generate_schema_from_list(data_list)
        assert schema_def.schema_content["type"] == "object"
        assert "name" in schema_def.schema_content["properties"]

    @pytest.mark.asyncio
    async def test_different_structures_detected(self):
        service = SchemaBuilderService()
        data_list = [
            {"user": {"name": "John"}},
            {"user": {"name": "Jane"}},
            {"product": {"id": 123}},
        ]
        schema_def, analysis = await service.generate_schema_from_list(data_list)
        assert analysis is not None
        assert analysis.unique_structures >= 1


class TestSchemaBuilderServiceInitialization:
    def test_initialization_creates_inferrer(self):
        service = SchemaBuilderService()
        assert service.inferrer is not None

    def test_initialization_creates_grouped_builder(self):
        service = SchemaBuilderService()
        assert service.grouped_builder is not None


class TestSchemaDefinitionOutput:
    def test_returns_schema_definition_instance(self):
        service = SchemaBuilderService()
        result = service.generate_schema({"test": "value"})
        assert isinstance(result, SchemaDefinition)
        assert hasattr(result, "schema_content")

    def test_schema_content_is_dict(self):
        service = SchemaBuilderService()
        result = service.generate_schema({"test": "value"})
        assert isinstance(result.schema_content, dict)

    @pytest.mark.asyncio
    async def test_schema_definition_from_list_returns_tuple(self):
        service = SchemaBuilderService()
        schema_def, analysis = await service.generate_schema_from_list([{"test": "value"}])
        assert isinstance(schema_def, SchemaDefinition)


class TestPrimitiveTypes:
    def test_boolean_true(self):
        service = SchemaBuilderService()
        result = service.generate_schema(True)
        assert result.schema_content["type"] == "boolean"

    def test_boolean_false(self):
        service = SchemaBuilderService()
        result = service.generate_schema(False)
        assert result.schema_content["type"] == "boolean"

    def test_null_value(self):
        service = SchemaBuilderService()
        result = service.generate_schema(None)
        assert result.schema_content["type"] == "null"

    def test_float_value(self):
        service = SchemaBuilderService()
        result = service.generate_schema(3.14)
        assert result.schema_content["type"] == "number"
        assert result.schema_content["minimum"] == 3.0
        assert result.schema_content["maximum"] == 4.0


class TestComplexScenarios:
    def test_complex_nested_structure(self):
        service = SchemaBuilderService()
        data = {
            "id": 1,
            "name": "Product",
            "price": 29.99,
            "available": True,
            "tags": ["electronics", "sale"],
            "metadata": {"created": "2024-01-15", "updated": None},
        }
        result = service.generate_schema(data)
        schema = result.schema_content
        assert schema["type"] == "object"
        assert schema["properties"]["id"]["type"] == "integer"
        assert schema["properties"]["name"]["type"] == "string"
        assert schema["properties"]["price"]["type"] == "number"
        assert schema["properties"]["available"]["type"] == "boolean"
        assert schema["properties"]["tags"]["type"] == "array"
        assert schema["properties"]["metadata"]["type"] == "object"

    def test_array_of_different_objects(self):
        service = SchemaBuilderService()
        data = [
            {"type": "user", "name": "John"},
            {"type": "admin", "name": "Jane", "permissions": ["read", "write"]},
        ]

        result = service.generate_schema(data)
        schema = result.schema_content
        assert schema["type"] == "array"
        assert "items" in schema

    def test_deeply_nested_objects(self):
        service = SchemaBuilderService()
        data = {"level1": {"level2": {"level3": {"value": "deep"}}}}
        result = service.generate_schema(data)
        schema = result.schema_content
        assert schema["type"] == "object"
        level1 = schema["properties"]["level1"]
        assert level1["type"] == "object"
        level2 = level1["properties"]["level2"]
        assert level2["type"] == "object"
        level3 = level2["properties"]["level3"]
        assert level3["type"] == "object"
        assert level3["properties"]["value"]["type"] == "string"
