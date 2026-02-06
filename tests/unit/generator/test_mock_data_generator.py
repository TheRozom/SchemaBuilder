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
