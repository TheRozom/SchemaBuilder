from unittest.mock import patch

import pytest
from jsonschema import Draft7Validator

from src.bl.generator import MockDataGenerator
from src.shared.exceptions import MockDataGenerationError


class TestMockDataGenerator:
    @pytest.fixture
    def generator(self):
        return MockDataGenerator(seed=42)

    def test_generate_from_schema_single_record(self, generator):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
                "active": {"type": "boolean"},
            },
        }
        result = generator.generate_from_schema(schema, count=1)
        assert isinstance(result, dict)
        assert "name" in result
        assert "age" in result
        assert "active" in result
        assert isinstance(result["name"], str)
        assert isinstance(result["age"], int)
        assert isinstance(result["active"], bool)

    def test_generate_from_schema_multiple_records(self, generator):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "score": {"type": "number"},
            },
        }
        result = generator.generate_from_schema(schema, count=5)
        assert isinstance(result, list)
        assert len(result) == 5

        for record in result:
            assert "name" in record
            assert "score" in record

    def test_generate_with_enum(self, generator):
        schema = {
            "type": "object",
            "properties": {"status": {"type": "string", "enum": ["active", "inactive", "pending"]}},
        }
        result = generator.generate_from_schema(schema, count=10)

        for record in result:
            assert record["status"] in ["active", "inactive", "pending"]

    def test_generate_with_field_name_patterns(self, generator):
        schema = {
            "type": "object",
            "properties": {
                "user_email": {"type": "string"},
                "password": {"type": "string"},
                "first_name": {"type": "string"},
            },
        }
        result = generator.generate_from_schema(schema, count=1)
        assert "@" in result["user_email"]
        assert isinstance(result["password"], str)
        assert isinstance(result["first_name"], str)

    def test_generate_integer_with_constraints(self, generator):
        schema = {
            "type": "object",
            "properties": {"score": {"type": "integer", "minimum": 0, "maximum": 100}},
        }
        result = generator.generate_from_schema(schema, count=10)

        for record in result:
            assert 0 <= record["score"] <= 100

    def test_generate_number_with_constraints(self, generator):
        schema = {
            "type": "object",
            "properties": {"price": {"type": "number", "minimum": 10.0, "maximum": 50.0}},
        }
        result = generator.generate_from_schema(schema, count=10)

        for record in result:
            assert 10.0 <= record["price"] <= 50.0

    def test_generate_string_with_length_constraints(self, generator):
        schema = {
            "type": "object",
            "properties": {"code": {"type": "string", "minLength": 5, "maxLength": 10}},
        }
        result = generator.generate_from_schema(schema, count=10)

        for record in result:
            assert 5 <= len(record["code"]) <= 10

    def test_generate_array(self, generator):
        schema = {
            "type": "object",
            "properties": {
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 2,
                    "maxItems": 5,
                }
            },
        }
        result = generator.generate_from_schema(schema, count=1)
        assert isinstance(result["tags"], list)
        assert 2 <= len(result["tags"]) <= 5
        assert all(isinstance(tag, str) for tag in result["tags"])

    def test_generate_nested_object(self, generator):
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "age": {"type": "integer"},
                    },
                }
            },
        }
        result = generator.generate_from_schema(schema, count=1)
        assert isinstance(result["user"], dict)
        assert "name" in result["user"]
        assert "age" in result["user"]

    def test_generate_null_type(self, generator):
        schema = {
            "type": "object",
            "properties": {"optional_field": {"type": "null"}},
        }
        result = generator.generate_from_schema(schema, count=1)
        assert result["optional_field"] is None

    def test_with_seed(self):
        gen = MockDataGenerator(seed=123)
        schema = {
            "type": "object",
            "properties": {"value": {"type": "integer", "minimum": 0, "maximum": 1000}},
        }
        result = gen.generate_from_schema(schema, count=1)
        assert 0 <= result["value"] <= 1000

    def test_pattern_strategy_handles_regex(self, generator):
        schema = {
            "type": "object",
            "properties": {"code": {"type": "string", "pattern": r"\d{4}"}},
        }
        result = generator.generate_from_schema(schema, count=1)
        if result.get("code"):
            assert isinstance(result["code"], str)

    def test_pattern_strategy_handles_pattern(self, generator):
        schema = {
            "type": "object",
            "properties": {"value": {"type": "string", "pattern": r"^\d+$"}},
        }
        result = generator.generate_from_schema(schema, count=1)
        assert isinstance(result["value"], str)

    def test_generate_property_anyof_picks_valid_type(self, generator):
        schema = {
            "type": "object",
            "properties": {"value": {"anyOf": [{"type": "string"}, {"type": "integer"}]}},
        }
        results = generator.generate_from_schema(schema, count=20)
        for record in results:
            assert isinstance(record["value"], (str, int))

    def test_generate_property_oneof_picks_valid_type(self, generator):
        schema = {
            "type": "object",
            "properties": {"value": {"oneOf": [{"type": "string"}, {"type": "boolean"}]}},
        }
        results = generator.generate_from_schema(schema, count=20)
        for record in results:
            assert isinstance(record["value"], (str, bool))

    def test_generate_property_allof_merges_constraints(self, generator):
        schema = {
            "type": "object",
            "properties": {
                "value": {
                    "allOf": [
                        {"type": "integer", "minimum": 0},
                        {"maximum": 100},
                    ]
                }
            },
        }
        results = generator.generate_from_schema(schema, count=20)
        for record in results:
            assert isinstance(record["value"], int)
            assert 0 <= record["value"] <= 100

    def test_generate_property_allof_merges_overlapping_object_property_constraints(
        self, generator
    ):
        schema = {
            "allOf": [
                {
                    "type": "object",
                    "properties": {"score": {"type": "integer", "minimum": 10}},
                },
                {
                    "type": "object",
                    "properties": {"score": {"maximum": 20}},
                },
            ]
        }
        results = generator.generate_from_schema(schema, count=30)
        for record in results:
            assert 10 <= record["score"] <= 20

    def test_generate_property_allof_intersects_enum_values(self, generator):
        schema = {
            "type": "object",
            "properties": {
                "status": {
                    "allOf": [
                        {"type": "string", "enum": ["active", "pending"]},
                        {"enum": ["pending", "archived"]},
                    ]
                }
            },
        }
        results = generator.generate_from_schema(schema, count=20)
        for record in results:
            assert record["status"] == "pending"

    def test_generate_anyof_randomness(self):
        gen = MockDataGenerator()
        schema = {
            "type": "object",
            "properties": {"value": {"anyOf": [{"type": "string"}, {"type": "integer"}]}},
        }
        results = gen.generate_from_schema(schema, count=50)
        types_seen = {type(r["value"]) for r in results}
        assert len(types_seen) > 1

    def test_generate_anyof_with_null(self):
        gen = MockDataGenerator()
        schema = {
            "type": "object",
            "properties": {"value": {"anyOf": [{"type": "string"}, {"type": "null"}]}},
        }
        results = gen.generate_from_schema(
            schema, count=50, mode="strict_valid", null_probability=0.5
        )
        has_none = any(r["value"] is None for r in results)
        has_str = any(isinstance(r["value"], str) for r in results)
        assert has_none and has_str

    def test_generate_anyof_with_null_probability_zero_avoids_null(self):
        gen = MockDataGenerator()
        schema = {
            "type": "object",
            "properties": {"value": {"anyOf": [{"type": "string"}, {"type": "null"}]}},
        }
        results = gen.generate_from_schema(schema, count=30, null_probability=0.0)
        assert all(isinstance(r["value"], str) for r in results)

    def test_generate_top_level_anyof(self):
        gen = MockDataGenerator()
        schema = {
            "anyOf": [
                {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                },
                {
                    "type": "object",
                    "properties": {"age": {"type": "integer"}},
                },
            ]
        }
        results = gen.generate_from_schema(schema, count=50)
        has_name = any("name" in r for r in results)
        has_age = any("age" in r for r in results)
        assert has_name and has_age

    def test_generate_top_level_anyof_prefers_richer_branch(self):
        gen = MockDataGenerator()
        schema = {
            "anyOf": [
                {"type": "object", "properties": {}},
                {"type": "object", "properties": {"name": {"type": "string"}}},
            ]
        }
        results = gen.generate_from_schema(schema, count=20)
        assert all("name" in r for r in results)

    def test_meaningful_mode_allows_null_only_schema(self):
        gen = MockDataGenerator(seed=1)
        schema = {
            "type": "object",
            "properties": {
                "value": {"type": "null"},
            },
        }
        result = gen.generate_from_schema(
            schema, count=1, mode="meaningful", min_populated_fields=1
        )
        assert result == {"value": None}

    def test_generate_top_level_allof(self, generator):
        schema = {
            "allOf": [
                {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                },
                {
                    "type": "object",
                    "properties": {"age": {"type": "integer"}},
                },
            ]
        }
        result = generator.generate_from_schema(schema, count=1)
        assert "name" in result
        assert "age" in result
        assert isinstance(result["name"], str)
        assert isinstance(result["age"], int)

    def test_generate_array_items_with_anyof(self, generator):
        schema = {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {"anyOf": [{"type": "string"}, {"type": "integer"}]},
                    "minItems": 5,
                    "maxItems": 5,
                }
            },
        }
        result = generator.generate_from_schema(schema, count=1)
        assert isinstance(result["items"], list)
        assert len(result["items"]) == 5
        for item in result["items"]:
            assert isinstance(item, (str, int))

    def test_generate_nested_object_with_anyof(self, generator):
        schema = {
            "type": "object",
            "properties": {
                "wrapper": {
                    "type": "object",
                    "properties": {"value": {"anyOf": [{"type": "string"}, {"type": "integer"}]}},
                }
            },
        }
        result = generator.generate_from_schema(schema, count=1)
        assert isinstance(result["wrapper"], dict)
        assert isinstance(result["wrapper"]["value"], (str, int))

    def test_seed_propagation_in_arrays(self):
        schema = {
            "type": "object",
            "properties": {
                "tags": {
                    "type": "array",
                    "items": {"type": "integer", "minimum": 0, "maximum": 1000},
                    "minItems": 3,
                    "maxItems": 3,
                }
            },
        }
        gen1 = MockDataGenerator(seed=99)
        result1 = gen1.generate_from_schema(schema, count=1)
        gen2 = MockDataGenerator(seed=99)
        result2 = gen2.generate_from_schema(schema, count=1)
        assert result1["tags"] == result2["tags"]

    def test_seed_propagation_in_objects(self):
        schema = {
            "type": "object",
            "properties": {
                "nested": {
                    "type": "object",
                    "properties": {
                        "x": {"type": "integer", "minimum": 0, "maximum": 1000},
                        "y": {"type": "integer", "minimum": 0, "maximum": 1000},
                    },
                }
            },
        }
        gen1 = MockDataGenerator(seed=99)
        result1 = gen1.generate_from_schema(schema, count=1)
        gen2 = MockDataGenerator(seed=99)
        result2 = gen2.generate_from_schema(schema, count=1)
        assert result1["nested"] == result2["nested"]


class TestMockDataValidation:
    @pytest.fixture
    def generator(self):
        return MockDataGenerator()

    def test_generated_data_validates_against_schema(self, generator):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string", "minLength": 1, "maxLength": 50},
                "age": {"type": "integer", "minimum": 0, "maximum": 150},
                "active": {"type": "boolean"},
            },
            "required": ["name", "age", "active"],
            "additionalProperties": False,
        }
        results = generator.generate_from_schema(schema, count=20)
        validator = Draft7Validator(schema)
        for record in results:
            errors = list(validator.iter_errors(record))
            assert not errors, f"Validation errors: {[e.message for e in errors]}"

    def test_generated_data_with_patterns_validates(self, generator):
        schema = {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "pattern": r"^[A-Z]{3}-\d{4}$",
                },
                "hex": {
                    "type": "string",
                    "pattern": r"^[0-9a-f]+$",
                },
            },
            "required": ["code", "hex"],
            "additionalProperties": False,
        }
        results = generator.generate_from_schema(schema, count=20)
        validator = Draft7Validator(schema)
        for record in results:
            errors = list(validator.iter_errors(record))
            assert not errors, f"Validation errors: {[e.message for e in errors]}"

    def test_generated_data_with_enum_validates(self, generator):
        schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["active", "inactive"]},
                "count": {"type": "integer", "minimum": 0, "maximum": 10},
            },
            "required": ["status", "count"],
            "additionalProperties": False,
        }
        results = generator.generate_from_schema(schema, count=20)
        validator = Draft7Validator(schema)
        for record in results:
            errors = list(validator.iter_errors(record))
            assert not errors, f"Validation errors: {[e.message for e in errors]}"

    def test_generated_data_with_nested_objects_validates(self, generator):
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "age": {"type": "integer", "minimum": 0},
                    },
                    "required": ["name", "age"],
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                    "maxItems": 3,
                },
            },
            "required": ["user", "tags"],
            "additionalProperties": False,
        }
        results = generator.generate_from_schema(schema, count=10)
        validator = Draft7Validator(schema)
        for record in results:
            errors = list(validator.iter_errors(record))
            assert not errors, f"Validation errors: {[e.message for e in errors]}"

    def test_retry_produces_valid_record_after_initial_failure(self):
        generator = MockDataGenerator()
        call_count = 0
        original_generate = generator._generate_single_record

        def flaky_generate(schema, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                return {"name": 12345}
            return original_generate(schema, **kwargs)

        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
            "additionalProperties": False,
        }

        with patch.object(generator, "_generate_single_record", side_effect=flaky_generate):
            result = generator.generate_from_schema(schema, count=1)

        assert isinstance(result["name"], str)
        assert call_count == 3

    def test_raises_error_when_all_retries_fail(self):
        generator = MockDataGenerator()

        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
            "additionalProperties": False,
        }

        with (
            patch.object(generator, "_generate_single_record", return_value={"name": 12345}),
            pytest.raises(MockDataGenerationError) as exc_info,
        ):
            generator.generate_from_schema(schema, count=1)

        assert "Failed to generate valid mock data" in str(exc_info.value)
        assert exc_info.value.validation_errors

    def test_generated_data_with_anyof_validates(self, generator):
        schema = {
            "type": "object",
            "properties": {
                "value": {"anyOf": [{"type": "string"}, {"type": "integer"}]},
            },
            "required": ["value"],
            "additionalProperties": False,
        }
        results = generator.generate_from_schema(schema, count=20)
        validator = Draft7Validator(schema)
        for record in results:
            errors = list(validator.iter_errors(record))
            assert not errors, f"Validation errors: {[e.message for e in errors]}"
