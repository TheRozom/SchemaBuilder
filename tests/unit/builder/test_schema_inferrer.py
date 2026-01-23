"""Comprehensive unit tests for SchemaInferrer class."""

import pytest
from unittest.mock import patch

from src.bl.builder.inferrers import SchemaInferrer
from src.shared.models import SchemaNode, SchemaType


class TestSchemaInferrerPrimitiveTypes:
    """Tests for primitive type inference."""

    def test_infer_null(self):
        """Null values should infer to NULL type."""
        inferrer = SchemaInferrer()
        schema = inferrer.infer(None)

        assert schema.type == SchemaType.NULL

    def test_infer_boolean_true(self):
        """Boolean True should infer to BOOLEAN type."""
        inferrer = SchemaInferrer()
        schema = inferrer.infer(True)

        assert schema.type == SchemaType.BOOLEAN

    def test_infer_boolean_false(self):
        """Boolean False should infer to BOOLEAN type."""
        inferrer = SchemaInferrer()
        schema = inferrer.infer(False)

        assert schema.type == SchemaType.BOOLEAN

    def test_infer_integer_positive(self):
        """Positive integer should infer to INTEGER type with constraints."""
        inferrer = SchemaInferrer()
        schema = inferrer.infer(42)

        assert schema.type == SchemaType.INTEGER
        assert schema.minimum == 0
        assert schema.maximum == 42

    def test_infer_integer_zero(self):
        """Zero should infer to INTEGER type with constraints."""
        inferrer = SchemaInferrer()
        schema = inferrer.infer(0)

        assert schema.type == SchemaType.INTEGER
        assert schema.minimum == 0
        assert schema.maximum == 0

    def test_infer_integer_large(self):
        """Large integer should infer to INTEGER type with correct maximum."""
        inferrer = SchemaInferrer()
        schema = inferrer.infer(999999)

        assert schema.type == SchemaType.INTEGER
        assert schema.minimum == 0
        assert schema.maximum == 999999

    def test_infer_float(self):
        """Float should infer to NUMBER type."""
        inferrer = SchemaInferrer()
        schema = inferrer.infer(3.14)

        assert schema.type == SchemaType.NUMBER
        assert schema.minimum == 0

    def test_infer_float_zero(self):
        """Float zero should infer to NUMBER type."""
        inferrer = SchemaInferrer()
        schema = inferrer.infer(0.0)

        assert schema.type == SchemaType.NUMBER
        assert schema.minimum == 0


class TestSchemaInferrerStringPatterns:
    """Tests for string inference with pattern matching."""

    def test_infer_string_simple(self):
        """Simple string should infer to STRING type with length constraints."""
        inferrer = SchemaInferrer()
        schema = inferrer.infer("hello")

        assert schema.type == SchemaType.STRING
        assert schema.minLength == 0
        assert schema.maxLength == 5

    def test_infer_string_empty(self):
        """Empty string should infer to STRING type with maxLength=0."""
        inferrer = SchemaInferrer()
        schema = inferrer.infer("")

        assert schema.type == SchemaType.STRING
        assert schema.minLength == 0
        assert schema.maxLength == 0

    def test_infer_string_email_pattern(self):
        """Email string should match email pattern."""
        inferrer = SchemaInferrer()
        schema = inferrer.infer("user@example.com")

        assert schema.type == SchemaType.STRING
        assert schema.pattern is not None
        assert "email" in schema.pattern.lower() or "@" in schema.pattern

    def test_infer_string_uuid_pattern(self):
        """UUID string should match uuid pattern."""
        inferrer = SchemaInferrer()
        schema = inferrer.infer("550e8400-e29b-41d4-a716-446655440000")

        assert schema.type == SchemaType.STRING
        assert schema.pattern is not None

    def test_infer_string_uuid_uppercase(self):
        """Uppercase UUID should match uuid pattern (case insensitive)."""
        inferrer = SchemaInferrer()
        schema = inferrer.infer("550E8400-E29B-41D4-A716-446655440000")

        assert schema.type == SchemaType.STRING
        assert schema.pattern is not None

    def test_infer_string_ipv4_pattern(self):
        """IPv4 address should match ipv4 pattern."""
        inferrer = SchemaInferrer()
        schema = inferrer.infer("192.168.1.1")

        assert schema.type == SchemaType.STRING
        assert schema.pattern is not None

    def test_infer_string_date_pattern(self):
        """ISO date should match date pattern."""
        inferrer = SchemaInferrer()
        schema = inferrer.infer("2024-01-15")

        assert schema.type == SchemaType.STRING
        assert schema.pattern is not None

    def test_infer_string_datetime_pattern(self):
        """ISO datetime should match datetime pattern."""
        inferrer = SchemaInferrer()
        schema = inferrer.infer("2024-01-15T10:30:00Z")

        assert schema.type == SchemaType.STRING
        assert schema.pattern is not None

    def test_infer_string_datetime_with_offset(self):
        """ISO datetime with timezone offset should match datetime pattern."""
        inferrer = SchemaInferrer()
        schema = inferrer.infer("2024-01-15T10:30:00+05:00")

        assert schema.type == SchemaType.STRING
        assert schema.pattern is not None

    def test_infer_string_datetime_with_milliseconds(self):
        """ISO datetime with milliseconds should match datetime pattern."""
        inferrer = SchemaInferrer()
        schema = inferrer.infer("2024-01-15T10:30:00.123Z")

        assert schema.type == SchemaType.STRING
        assert schema.pattern is not None


class TestSchemaInferrerUnknownStrings:
    """Tests for unknown string samples collection."""

    def test_unknown_string_collected(self):
        """Unknown string should be collected in unknown_samples."""
        inferrer = SchemaInferrer()
        inferrer.infer("random text", path="field1")

        assert "field1" in inferrer.unknown_samples
        assert "random text" in inferrer.unknown_samples["field1"]

    def test_unknown_strings_same_path(self):
        """Multiple unknown strings at same path should be collected."""
        inferrer = SchemaInferrer()
        inferrer.infer("first value", path="field1")
        inferrer.infer("second value", path="field1")

        assert "field1" in inferrer.unknown_samples
        assert "first value" in inferrer.unknown_samples["field1"]
        assert "second value" in inferrer.unknown_samples["field1"]

    def test_unknown_strings_different_paths(self):
        """Unknown strings at different paths should be tracked separately."""
        inferrer = SchemaInferrer()
        inferrer.infer("value1", path="field1")
        inferrer.infer("value2", path="field2")

        assert "field1" in inferrer.unknown_samples
        assert "field2" in inferrer.unknown_samples
        assert "value1" in inferrer.unknown_samples["field1"]
        assert "value2" in inferrer.unknown_samples["field2"]

    def test_duplicate_unknown_string_not_added(self):
        """Duplicate unknown string should not be added twice."""
        inferrer = SchemaInferrer()
        inferrer.infer("same value", path="field1")
        inferrer.infer("same value", path="field1")

        assert len(inferrer.unknown_samples["field1"]) == 1

    def test_pattern_matched_string_not_collected(self):
        """String matching a pattern should NOT be collected as unknown."""
        inferrer = SchemaInferrer()
        inferrer.infer("user@example.com", path="email_field")

        assert "email_field" not in inferrer.unknown_samples

    @patch("src.bl.builder.inferrers.schema_inferrer.settings")
    def test_unknown_samples_respects_max_limit(self, mock_settings):
        """Unknown samples should respect INFERENCE_MAX_SAMPLES limit."""
        mock_settings.INFERENCE_MAX_SAMPLES = 3

        inferrer = SchemaInferrer()
        for i in range(5):
            inferrer.infer(f"value_{i}", path="field1")

        assert len(inferrer.unknown_samples["field1"]) == 3


class TestSchemaInferrerArrays:
    """Tests for array inference."""

    def test_infer_empty_array(self):
        """Empty array should infer to ARRAY type with no items schema."""
        inferrer = SchemaInferrer()
        schema = inferrer.infer([])

        assert schema.type == SchemaType.ARRAY
        assert schema.minItems == 0
        assert schema.maxItems == 0
        assert schema.items is None

    def test_infer_array_single_integer(self):
        """Array with single integer should have INTEGER items schema."""
        inferrer = SchemaInferrer()
        schema = inferrer.infer([42])

        assert schema.type == SchemaType.ARRAY
        assert schema.minItems == 0
        assert schema.maxItems == 1
        assert schema.items is not None
        assert schema.items.type == SchemaType.INTEGER

    def test_infer_array_multiple_integers(self):
        """Array with multiple integers should merge INTEGER items schemas."""
        inferrer = SchemaInferrer()
        schema = inferrer.infer([10, 20, 30])

        assert schema.type == SchemaType.ARRAY
        assert schema.maxItems == 3
        assert schema.items.type == SchemaType.INTEGER
        assert schema.items.maximum == 30

    def test_infer_array_strings(self):
        """Array with strings should have STRING items schema."""
        inferrer = SchemaInferrer()
        schema = inferrer.infer(["hello", "world"])

        assert schema.type == SchemaType.ARRAY
        assert schema.items.type == SchemaType.STRING

    def test_infer_array_mixed_types_uses_anyof(self):
        """Array with mixed types should use anyOf in items schema."""
        inferrer = SchemaInferrer()
        schema = inferrer.infer([42, "hello"])

        assert schema.type == SchemaType.ARRAY
        assert schema.items is not None
        # Mixed types result in anyOf
        assert len(schema.items.anyOf) == 2

    def test_infer_array_objects(self):
        """Array with objects should have OBJECT items schema."""
        inferrer = SchemaInferrer()
        schema = inferrer.infer([{"name": "John"}, {"name": "Jane"}])

        assert schema.type == SchemaType.ARRAY
        assert schema.items.type == SchemaType.OBJECT
        assert "name" in schema.items.properties

    def test_infer_nested_arrays(self):
        """Nested arrays should be properly inferred."""
        inferrer = SchemaInferrer()
        schema = inferrer.infer([[1, 2], [3, 4]])

        assert schema.type == SchemaType.ARRAY
        assert schema.items.type == SchemaType.ARRAY
        assert schema.items.items.type == SchemaType.INTEGER


class TestSchemaInferrerObjects:
    """Tests for object inference."""

    def test_infer_empty_object(self):
        """Empty object should infer to OBJECT type with no properties."""
        inferrer = SchemaInferrer()
        schema = inferrer.infer({})

        assert schema.type == SchemaType.OBJECT
        assert len(schema.properties) == 0
        assert schema.additionalProperties is False

    def test_infer_object_single_property(self):
        """Object with single property should be properly inferred."""
        inferrer = SchemaInferrer()
        schema = inferrer.infer({"name": "John"})

        assert schema.type == SchemaType.OBJECT
        assert "name" in schema.properties
        assert schema.properties["name"].type == SchemaType.STRING
        assert schema.additionalProperties is False

    def test_infer_object_multiple_properties(self):
        """Object with multiple properties should all be inferred."""
        inferrer = SchemaInferrer()
        schema = inferrer.infer({"name": "John", "age": 30, "active": True})

        assert schema.type == SchemaType.OBJECT
        assert schema.properties["name"].type == SchemaType.STRING
        assert schema.properties["age"].type == SchemaType.INTEGER
        assert schema.properties["active"].type == SchemaType.BOOLEAN

    def test_infer_object_nested(self):
        """Nested object should be properly inferred."""
        inferrer = SchemaInferrer()
        schema = inferrer.infer({"user": {"name": "John", "email": "john@example.com"}})

        assert schema.type == SchemaType.OBJECT
        assert "user" in schema.properties
        assert schema.properties["user"].type == SchemaType.OBJECT
        assert "name" in schema.properties["user"].properties
        assert "email" in schema.properties["user"].properties

    def test_infer_object_with_array_property(self):
        """Object with array property should be properly inferred."""
        inferrer = SchemaInferrer()
        schema = inferrer.infer({"tags": ["python", "testing"]})

        assert schema.type == SchemaType.OBJECT
        assert schema.properties["tags"].type == SchemaType.ARRAY
        assert schema.properties["tags"].items.type == SchemaType.STRING

    def test_infer_object_with_null_property(self):
        """Object with null property should be properly inferred."""
        inferrer = SchemaInferrer()
        schema = inferrer.infer({"name": "John", "middle_name": None})

        assert schema.type == SchemaType.OBJECT
        assert schema.properties["middle_name"].type == SchemaType.NULL

    def test_infer_object_additional_properties_false(self):
        """Object should always have additionalProperties=False."""
        inferrer = SchemaInferrer()
        schema = inferrer.infer({"key": "value"})

        assert schema.additionalProperties is False


class TestSchemaInferrerPathTracking:
    """Tests for path tracking in nested structures."""

    def test_path_empty_at_root(self):
        """Root level inference should use empty path."""
        inferrer = SchemaInferrer()
        inferrer.infer("unknown string")

        assert "" in inferrer.unknown_samples

    def test_path_tracking_object_properties(self):
        """Object properties should have correct path."""
        inferrer = SchemaInferrer()
        inferrer.infer({"name": "unknown value"})

        assert "name" in inferrer.unknown_samples

    def test_path_tracking_nested_object(self):
        """Nested object properties should have dotted path."""
        inferrer = SchemaInferrer()
        inferrer.infer({"user": {"name": "unknown value"}})

        assert "user.name" in inferrer.unknown_samples

    def test_path_tracking_deeply_nested(self):
        """Deeply nested properties should have full dotted path."""
        inferrer = SchemaInferrer()
        inferrer.infer({"level1": {"level2": {"level3": "unknown value"}}})

        assert "level1.level2.level3" in inferrer.unknown_samples

    def test_path_tracking_array_items(self):
        """Array items should have [] in path."""
        inferrer = SchemaInferrer()
        inferrer.infer(["unknown string"], path="items")

        assert "items[]" in inferrer.unknown_samples

    def test_path_tracking_array_of_objects(self):
        """Array of objects should track paths correctly."""
        inferrer = SchemaInferrer()
        inferrer.infer({"users": [{"name": "unknown value"}]})

        assert "users[].name" in inferrer.unknown_samples


class TestSchemaInferrerToDict:
    """Tests for SchemaNode.to_dict() conversion."""

    def test_to_dict_null(self):
        """Null schema should convert to dict correctly."""
        inferrer = SchemaInferrer()
        schema = inferrer.infer(None)
        result = schema.to_dict()

        assert result == {"type": "null"}

    def test_to_dict_boolean(self):
        """Boolean schema should convert to dict correctly."""
        inferrer = SchemaInferrer()
        schema = inferrer.infer(True)
        result = schema.to_dict()

        assert result == {"type": "boolean"}

    def test_to_dict_integer(self):
        """Integer schema should convert to dict with constraints."""
        inferrer = SchemaInferrer()
        schema = inferrer.infer(100)
        result = schema.to_dict()

        assert result["type"] == "integer"
        assert result["minimum"] == 0
        assert result["maximum"] == 100

    def test_to_dict_string_with_pattern(self):
        """String with pattern should include pattern in dict."""
        inferrer = SchemaInferrer()
        schema = inferrer.infer("user@example.com")
        result = schema.to_dict()

        assert result["type"] == "string"
        assert "pattern" in result
        assert result["minLength"] == 0

    def test_to_dict_array(self):
        """Array schema should convert to dict correctly."""
        inferrer = SchemaInferrer()
        schema = inferrer.infer([1, 2, 3])
        result = schema.to_dict()

        assert result["type"] == "array"
        assert "items" in result
        assert result["items"]["type"] == "integer"

    def test_to_dict_object(self):
        """Object schema should convert to dict correctly."""
        inferrer = SchemaInferrer()
        schema = inferrer.infer({"name": "John"})
        result = schema.to_dict()

        assert result["type"] == "object"
        assert "properties" in result
        assert "name" in result["properties"]
        assert result["additionalProperties"] is False

    def test_to_dict_excludes_none_values(self):
        """to_dict should exclude None values."""
        inferrer = SchemaInferrer()
        schema = inferrer.infer(True)
        result = schema.to_dict()

        # Boolean schema should only have "type"
        assert "pattern" not in result
        assert "minimum" not in result
        assert "items" not in result

    def test_to_dict_excludes_empty_lists(self):
        """to_dict should exclude empty lists."""
        inferrer = SchemaInferrer()
        schema = inferrer.infer({"key": "value"})
        result = schema.to_dict()

        assert "anyOf" not in result
        assert "oneOf" not in result
        assert "required" not in result


class TestSchemaInferrerEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_infer_negative_integer(self):
        """Negative integer should still set minimum=0."""
        inferrer = SchemaInferrer()
        schema = inferrer.infer(-5)

        assert schema.type == SchemaType.INTEGER
        assert schema.minimum == 0
        assert schema.maximum == -5

    def test_infer_negative_float(self):
        """Negative float should still set minimum=0."""
        inferrer = SchemaInferrer()
        schema = inferrer.infer(-3.14)

        assert schema.type == SchemaType.NUMBER
        assert schema.minimum == 0

    def test_infer_very_long_string(self):
        """Very long string should have correct maxLength."""
        inferrer = SchemaInferrer()
        long_string = "x" * 10000
        schema = inferrer.infer(long_string)

        assert schema.type == SchemaType.STRING
        assert schema.maxLength == 10000

    def test_infer_unicode_string(self):
        """Unicode string should be properly inferred."""
        inferrer = SchemaInferrer()
        schema = inferrer.infer("Hello 世界 🌍")

        assert schema.type == SchemaType.STRING
        assert schema.maxLength == len("Hello 世界 🌍")

    def test_infer_complex_nested_structure(self):
        """Complex nested structure should be fully inferred."""
        inferrer = SchemaInferrer()
        data = {
            "id": 1,
            "name": "Product",
            "price": 29.99,
            "available": True,
            "tags": ["electronics", "sale"],
            "metadata": {"created": "2024-01-15", "updated": None},
            "variants": [{"color": "red", "size": "S"}, {"color": "blue", "size": "M"}],
        }
        schema = inferrer.infer(data)

        assert schema.type == SchemaType.OBJECT
        assert schema.properties["id"].type == SchemaType.INTEGER
        assert schema.properties["name"].type == SchemaType.STRING
        assert schema.properties["price"].type == SchemaType.NUMBER
        assert schema.properties["available"].type == SchemaType.BOOLEAN
        assert schema.properties["tags"].type == SchemaType.ARRAY
        assert schema.properties["metadata"].type == SchemaType.OBJECT
        assert schema.properties["variants"].type == SchemaType.ARRAY

    def test_multiple_inferences_share_unknown_samples(self):
        """Multiple inferences on same inferrer should share unknown_samples."""
        inferrer = SchemaInferrer()

        inferrer.infer({"field1": "value1"})
        inferrer.infer({"field2": "value2"})

        assert "field1" in inferrer.unknown_samples
        assert "field2" in inferrer.unknown_samples

    def test_infer_with_custom_path(self):
        """Custom path should be used for tracking."""
        inferrer = SchemaInferrer()
        inferrer.infer("custom value", path="custom.path")

        assert "custom.path" in inferrer.unknown_samples

    def test_schema_node_is_returned(self):
        """All infer methods should return SchemaNode instances."""
        inferrer = SchemaInferrer()

        assert isinstance(inferrer.infer(None), SchemaNode)
        assert isinstance(inferrer.infer(True), SchemaNode)
        assert isinstance(inferrer.infer(42), SchemaNode)
        assert isinstance(inferrer.infer(3.14), SchemaNode)
        assert isinstance(inferrer.infer("hello"), SchemaNode)
        assert isinstance(inferrer.infer([]), SchemaNode)
        assert isinstance(inferrer.infer({}), SchemaNode)
