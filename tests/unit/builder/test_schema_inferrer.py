from unittest.mock import patch

from src.bl.builder.inferrers import SchemaInferrer
from src.shared.models import SchemaNode, SchemaType


class TestSchemaInferrerPrimitiveTypes:
    def test_infer_null(self):
        inferrer = SchemaInferrer()
        schema = inferrer.infer(None)
        assert schema.type == SchemaType.NULL

    def test_infer_boolean_true(self):
        inferrer = SchemaInferrer()
        schema = inferrer.infer(True)
        assert schema.type == SchemaType.BOOLEAN

    def test_infer_boolean_false(self):
        inferrer = SchemaInferrer()
        schema = inferrer.infer(False)
        assert schema.type == SchemaType.BOOLEAN

    def test_infer_integer_positive(self):
        inferrer = SchemaInferrer()
        schema = inferrer.infer(42)
        assert schema.type == SchemaType.INTEGER
        assert schema.minimum == 0
        assert schema.maximum == 42

    def test_infer_integer_zero(self):
        inferrer = SchemaInferrer()
        schema = inferrer.infer(0)
        assert schema.type == SchemaType.INTEGER
        assert schema.minimum == 0
        assert schema.maximum == 0

    def test_infer_integer_large(self):
        inferrer = SchemaInferrer()
        schema = inferrer.infer(999999)
        assert schema.type == SchemaType.INTEGER
        assert schema.minimum == 0
        assert schema.maximum == 999999

    def test_infer_float(self):
        inferrer = SchemaInferrer()
        schema = inferrer.infer(3.14)
        assert schema.type == SchemaType.NUMBER
        assert schema.minimum == 0
        assert schema.maximum == 3.14

    def test_infer_float_zero(self):
        inferrer = SchemaInferrer()
        schema = inferrer.infer(0.0)
        assert schema.type == SchemaType.NUMBER
        assert schema.minimum == 0.0
        assert schema.maximum == 0.0


class TestSchemaInferrerStringPatterns:
    def test_infer_string_simple(self):
        inferrer = SchemaInferrer()
        schema = inferrer.infer("hello")
        assert schema.type == SchemaType.STRING
        assert schema.minLength == 0
        assert schema.maxLength == 5

    def test_infer_string_empty(self):
        inferrer = SchemaInferrer()
        schema = inferrer.infer("")
        assert schema.type == SchemaType.STRING
        assert schema.minLength == 0
        assert schema.maxLength == 0

    def test_infer_string_email_pattern(self):
        inferrer = SchemaInferrer()
        schema = inferrer.infer("user@example.com")
        assert schema.type == SchemaType.STRING
        assert schema.pattern is not None
        assert "email" in schema.pattern.lower() or "@" in schema.pattern

    def test_infer_string_uuid_pattern(self):
        inferrer = SchemaInferrer()
        schema = inferrer.infer("550e8400-e29b-41d4-a716-446655440000")
        assert schema.type == SchemaType.STRING
        assert schema.pattern is not None

    def test_infer_string_uuid_uppercase(self):
        inferrer = SchemaInferrer()
        schema = inferrer.infer("550E8400-E29B-41D4-A716-446655440000")
        assert schema.type == SchemaType.STRING
        assert schema.pattern is not None

    def test_infer_string_ipv4_pattern(self):
        inferrer = SchemaInferrer()
        schema = inferrer.infer("192.168.1.1")
        assert schema.type == SchemaType.STRING
        assert schema.pattern is not None

    def test_infer_string_date_pattern(self):
        inferrer = SchemaInferrer()
        schema = inferrer.infer("2024-01-15")
        assert schema.type == SchemaType.STRING
        assert schema.pattern is not None

    def test_infer_string_datetime_pattern(self):
        inferrer = SchemaInferrer()
        schema = inferrer.infer("2024-01-15T10:30:00Z")
        assert schema.type == SchemaType.STRING
        assert schema.pattern is not None

    def test_infer_string_datetime_with_offset(self):
        inferrer = SchemaInferrer()
        schema = inferrer.infer("2024-01-15T10:30:00+05:00")
        assert schema.type == SchemaType.STRING
        assert schema.pattern is not None

    def test_infer_string_datetime_with_milliseconds(self):
        inferrer = SchemaInferrer()
        schema = inferrer.infer("2024-01-15T10:30:00.123Z")
        assert schema.type == SchemaType.STRING
        assert schema.pattern is not None


class TestSchemaInferrerPatternSpecificity:
    def test_five_digit_string_matches_zipcode_over_numbers_only(self):
        from src.bl.builder.config import PATTERN_REGISTRY

        inferrer = SchemaInferrer()
        schema = inferrer.infer("12345")
        assert schema.type == SchemaType.STRING
        assert schema.pattern is not None
        assert schema.pattern == PATTERN_REGISTRY["zipcode_us"].pattern


class TestSchemaInferrerUnknownStrings:
    def test_unknown_string_collected(self):
        inferrer = SchemaInferrer()
        inferrer.infer("random_text", path="field1")
        assert "field1" in inferrer.unknown_samples
        assert "random_text" in inferrer.unknown_samples["field1"]

    def test_unknown_strings_same_path(self):
        inferrer = SchemaInferrer()
        inferrer.infer("first_value", path="field1")
        inferrer.infer("second_value", path="field1")
        assert "field1" in inferrer.unknown_samples
        assert "first_value" in inferrer.unknown_samples["field1"]
        assert "second_value" in inferrer.unknown_samples["field1"]

    def test_unknown_strings_different_paths(self):
        inferrer = SchemaInferrer()
        inferrer.infer("value1", path="field1")
        inferrer.infer("value2", path="field2")
        assert "field1" in inferrer.unknown_samples
        assert "field2" in inferrer.unknown_samples
        assert "value1" in inferrer.unknown_samples["field1"]
        assert "value2" in inferrer.unknown_samples["field2"]

    def test_duplicate_unknown_string_not_added(self):
        inferrer = SchemaInferrer()
        inferrer.infer("same_value", path="field1")
        inferrer.infer("same_value", path="field1")
        assert len(inferrer.unknown_samples["field1"]) == 1

    def test_pattern_matched_string_not_collected(self):
        inferrer = SchemaInferrer()
        inferrer.infer("user@example.com", path="email_field")
        assert "email_field" not in inferrer.unknown_samples

    @patch("src.bl.builder.inferrers.schema_inferrer.settings")
    def test_unknown_samples_respects_max_limit(self, mock_settings):
        mock_settings.INFERENCE_MAX_SAMPLES = 3
        inferrer = SchemaInferrer()

        for i in range(5):
            inferrer.infer(f"value_{i}", path="field1")

        assert len(inferrer.unknown_samples["field1"]) == 3


class TestSchemaInferrerArrays:
    def test_infer_empty_array(self):
        inferrer = SchemaInferrer()
        schema = inferrer.infer([])
        assert schema.type == SchemaType.ARRAY
        assert schema.minItems == 0
        assert schema.maxItems == 0
        assert schema.items is None

    def test_infer_array_single_integer(self):
        inferrer = SchemaInferrer()
        schema = inferrer.infer([42])
        assert schema.type == SchemaType.ARRAY
        assert schema.minItems == 0
        assert schema.maxItems == 1
        assert schema.items is not None
        assert schema.items.type == SchemaType.INTEGER

    def test_infer_array_multiple_integers(self):
        inferrer = SchemaInferrer()
        schema = inferrer.infer([10, 20, 30])
        assert schema.type == SchemaType.ARRAY
        assert schema.maxItems == 3
        assert schema.items.type == SchemaType.INTEGER
        assert schema.items.maximum == 30

    def test_infer_array_strings(self):
        inferrer = SchemaInferrer()
        schema = inferrer.infer(["hello", "world"])
        assert schema.type == SchemaType.ARRAY
        assert schema.items.type == SchemaType.STRING

    def test_infer_array_mixed_types_uses_anyof(self):
        inferrer = SchemaInferrer()
        schema = inferrer.infer([42, "hello"])
        assert schema.type == SchemaType.ARRAY
        assert schema.items is not None
        assert len(schema.items.anyOf) == 2

    def test_infer_array_objects(self):
        inferrer = SchemaInferrer()
        schema = inferrer.infer([{"name": "John"}, {"name": "Jane"}])
        assert schema.type == SchemaType.ARRAY
        assert schema.items.type == SchemaType.OBJECT
        assert "name" in schema.items.properties

    def test_infer_nested_arrays(self):
        inferrer = SchemaInferrer()
        schema = inferrer.infer([[1, 2], [3, 4]])
        assert schema.type == SchemaType.ARRAY
        assert schema.items.type == SchemaType.ARRAY
        assert schema.items.items.type == SchemaType.INTEGER


class TestSchemaInferrerObjects:
    def test_infer_empty_object(self):
        inferrer = SchemaInferrer()
        schema = inferrer.infer({})
        assert schema.type == SchemaType.OBJECT
        assert len(schema.properties) == 0
        assert schema.additionalProperties is False

    def test_infer_object_single_property(self):
        inferrer = SchemaInferrer()
        schema = inferrer.infer({"name": "John"})
        assert schema.type == SchemaType.OBJECT
        assert "name" in schema.properties
        assert schema.properties["name"].type == SchemaType.STRING
        assert schema.additionalProperties is False

    def test_infer_object_multiple_properties(self):
        inferrer = SchemaInferrer()
        schema = inferrer.infer({"name": "John", "age": 30, "active": True})
        assert schema.type == SchemaType.OBJECT
        assert schema.properties["name"].type == SchemaType.STRING
        assert schema.properties["age"].type == SchemaType.INTEGER
        assert schema.properties["active"].type == SchemaType.BOOLEAN

    def test_infer_object_nested(self):
        inferrer = SchemaInferrer()
        schema = inferrer.infer({"user": {"name": "John", "email": "john@example.com"}})

        assert schema.type == SchemaType.OBJECT
        assert "user" in schema.properties
        assert schema.properties["user"].type == SchemaType.OBJECT
        assert "name" in schema.properties["user"].properties
        assert "email" in schema.properties["user"].properties

    def test_infer_object_with_array_property(self):
        inferrer = SchemaInferrer()
        schema = inferrer.infer({"tags": ["python", "testing"]})
        assert schema.type == SchemaType.OBJECT
        assert schema.properties["tags"].type == SchemaType.ARRAY
        assert schema.properties["tags"].items.type == SchemaType.STRING

    def test_infer_object_with_null_property(self):
        inferrer = SchemaInferrer()
        schema = inferrer.infer({"name": "John", "middle_name": None})
        assert schema.type == SchemaType.OBJECT
        assert schema.properties["middle_name"].type == SchemaType.NULL

    def test_infer_object_additional_properties_false(self):
        inferrer = SchemaInferrer()
        schema = inferrer.infer({"key": "value"})
        assert schema.additionalProperties is False


class TestSchemaInferrerPathTracking:
    def test_path_empty_at_root(self):
        inferrer = SchemaInferrer()
        inferrer.infer("unknown_str1ng")
        assert "" in inferrer.unknown_samples

    def test_path_tracking_object_properties(self):
        inferrer = SchemaInferrer()
        inferrer.infer({"name": "unknown_value1"})
        assert "name" in inferrer.unknown_samples

    def test_path_tracking_nested_object(self):
        inferrer = SchemaInferrer()
        inferrer.infer({"user": {"name": "unknown_value1"}})
        assert "user.name" in inferrer.unknown_samples

    def test_path_tracking_deeply_nested(self):
        inferrer = SchemaInferrer()
        inferrer.infer({"level1": {"level2": {"level3": "unknown_value1"}}})
        assert "level1.level2.level3" in inferrer.unknown_samples

    def test_path_tracking_array_items(self):
        inferrer = SchemaInferrer()
        inferrer.infer(["unknown_str1ng"], path="items")
        assert "items[]" in inferrer.unknown_samples

    def test_path_tracking_array_of_objects(self):
        inferrer = SchemaInferrer()
        inferrer.infer({"users": [{"name": "unknown_value1"}]})
        assert "users[].name" in inferrer.unknown_samples


class TestSchemaInferrerToDict:
    def test_to_dict_null(self):
        inferrer = SchemaInferrer()
        schema = inferrer.infer(None)
        result = schema.to_dict()
        assert result == {"type": "null"}

    def test_to_dict_boolean(self):
        inferrer = SchemaInferrer()
        schema = inferrer.infer(True)
        result = schema.to_dict()
        assert result == {"type": "boolean"}

    def test_to_dict_integer(self):
        inferrer = SchemaInferrer()
        schema = inferrer.infer(100)
        result = schema.to_dict()
        assert result["type"] == "integer"
        assert result["minimum"] == 0
        assert result["maximum"] == 100

    def test_to_dict_string_with_pattern(self):
        inferrer = SchemaInferrer()
        schema = inferrer.infer("user@example.com")
        result = schema.to_dict()
        assert result["type"] == "string"
        assert "pattern" in result
        assert result["minLength"] == 0

    def test_to_dict_array(self):
        inferrer = SchemaInferrer()
        schema = inferrer.infer([1, 2, 3])
        result = schema.to_dict()
        assert result["type"] == "array"
        assert "items" in result
        assert result["items"]["type"] == "integer"

    def test_to_dict_object(self):
        inferrer = SchemaInferrer()
        schema = inferrer.infer({"name": "John"})
        result = schema.to_dict()
        assert result["type"] == "object"
        assert "properties" in result
        assert "name" in result["properties"]
        assert result["additionalProperties"] is False

    def test_to_dict_excludes_none_values(self):
        inferrer = SchemaInferrer()
        schema = inferrer.infer(True)
        result = schema.to_dict()
        assert "pattern" not in result
        assert "minimum" not in result
        assert "items" not in result

    def test_to_dict_excludes_empty_lists(self):
        inferrer = SchemaInferrer()
        schema = inferrer.infer({"key": "value"})
        result = schema.to_dict()
        assert "anyOf" not in result
        assert "oneOf" not in result
        assert "required" not in result


class TestSchemaInferrerEdgeCases:
    def test_infer_negative_integer(self):
        inferrer = SchemaInferrer()
        schema = inferrer.infer(-5)
        assert schema.type == SchemaType.INTEGER
        assert schema.minimum == -5
        assert schema.maximum == -5

    def test_infer_negative_float(self):
        inferrer = SchemaInferrer()
        schema = inferrer.infer(-3.14)
        assert schema.type == SchemaType.NUMBER
        assert schema.minimum == -3.14
        assert schema.maximum == -3.14

    def test_infer_very_long_string(self):
        inferrer = SchemaInferrer()
        long_string = "x" * 10000
        schema = inferrer.infer(long_string)
        assert schema.type == SchemaType.STRING
        assert schema.maxLength == 10000

    def test_infer_unicode_string(self):
        inferrer = SchemaInferrer()
        schema = inferrer.infer("Hello 世界 🌍")
        assert schema.type == SchemaType.STRING
        assert schema.maxLength == len("Hello 世界 🌍")

    def test_infer_complex_nested_structure(self):
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
        inferrer = SchemaInferrer()
        inferrer.infer({"field1": "value1"})
        inferrer.infer({"field2": "value2"})
        assert "field1" in inferrer.unknown_samples
        assert "field2" in inferrer.unknown_samples

    def test_infer_with_custom_path(self):
        inferrer = SchemaInferrer()
        inferrer.infer("custom_value1", path="custom.path")
        assert "custom.path" in inferrer.unknown_samples

    def test_schema_node_is_returned(self):
        inferrer = SchemaInferrer()
        assert isinstance(inferrer.infer(None), SchemaNode)
        assert isinstance(inferrer.infer(True), SchemaNode)
        assert isinstance(inferrer.infer(42), SchemaNode)
        assert isinstance(inferrer.infer(3.14), SchemaNode)
        assert isinstance(inferrer.infer("hello"), SchemaNode)
        assert isinstance(inferrer.infer([]), SchemaNode)
        assert isinstance(inferrer.infer({}), SchemaNode)
