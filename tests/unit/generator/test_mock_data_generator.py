import pytest

from src.bl.generator import MockDataGenerator


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
        results = gen.generate_from_schema(schema, count=50)
        has_none = any(r["value"] is None for r in results)
        has_str = any(isinstance(r["value"], str) for r in results)
        assert has_none and has_str

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
