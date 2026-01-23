"""Tests for MockDataGenerator."""

import pytest
from src.bl.generator.mock_data_generator import MockDataGenerator


class TestMockDataGenerator:
    """Test suite for MockDataGenerator."""

    @pytest.fixture
    def generator(self):
        """Create a MockDataGenerator with fixed seed for reproducibility."""
        return MockDataGenerator(seed=42)

    def test_generate_email(self, generator):
        """Test email generation."""
        email = generator.generate_by_type("email")
        assert isinstance(email, str)
        assert "@" in email
        assert "." in email

    def test_generate_name(self, generator):
        """Test name generation."""
        name = generator.generate_by_type("name")
        assert isinstance(name, str)
        assert len(name) > 0

    def test_generate_phone(self, generator):
        """Test phone number generation."""
        phone = generator.generate_by_type("phone")
        assert isinstance(phone, str)
        # Should contain some digits
        assert any(c.isdigit() for c in phone)

    def test_generate_address(self, generator):
        """Test address generation."""
        address = generator.generate_by_type("address")
        assert isinstance(address, str)
        assert len(address) > 0

    def test_generate_url(self, generator):
        """Test URL generation."""
        url = generator.generate_by_type("url")
        assert isinstance(url, str)
        assert url.startswith("http")

    def test_generate_date(self, generator):
        """Test date generation."""
        date = generator.generate_by_type("date")
        assert isinstance(date, str)
        # Should look like a date
        assert "-" in date or "/" in date

    def test_generate_boolean(self, generator):
        """Test boolean generation."""
        boolean = generator.generate_by_type("boolean")
        assert isinstance(boolean, bool)

    def test_generate_id(self, generator):
        """Test ID/UUID generation."""
        id_value = generator.generate_by_type("id")
        assert isinstance(id_value, str)
        assert len(id_value) > 0

    def test_generate_price(self, generator):
        """Test price generation."""
        price = generator.generate_by_type("price")
        assert isinstance(price, (int, float))
        assert price >= 1
        assert price <= 1000

    def test_generate_unknown_type(self, generator):
        """Test generation with unknown type."""
        result = generator.generate_by_type("unknown_type")
        assert result is None

    def test_generate_by_name_pattern_first_name(self, generator):
        """Test generation based on field name - first name."""
        value = generator._generate_by_name_pattern("first_name")
        assert isinstance(value, str)
        assert len(value) > 0

    def test_generate_by_name_pattern_last_name(self, generator):
        """Test generation based on field name - last name."""
        value = generator._generate_by_name_pattern("last_name")
        assert isinstance(value, str)
        assert len(value) > 0

    def test_generate_by_name_pattern_age(self, generator):
        """Test generation based on field name - age."""
        value = generator._generate_by_name_pattern("age")
        assert isinstance(value, int)
        assert 18 <= value <= 80

    def test_generate_from_schema_single_record(self, generator):
        """Test generating a single record from schema."""
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
        """Test generating multiple records from schema."""
        schema = {
            "type": "object",
            "properties": {
                "email": {"type": "string", "format": "email"},
                "score": {"type": "number"},
            },
        }

        result = generator.generate_from_schema(schema, count=5)
        assert isinstance(result, list)
        assert len(result) == 5
        for record in result:
            assert "email" in record
            assert "score" in record

    def test_generate_with_enum(self, generator):
        """Test generation with enum constraint."""
        schema = {
            "type": "object",
            "properties": {"status": {"type": "string", "enum": ["active", "inactive", "pending"]}},
        }

        result = generator.generate_from_schema(schema, count=10)
        for record in result:
            assert record["status"] in ["active", "inactive", "pending"]

    def test_generate_with_format(self, generator):
        """Test generation respecting format property."""
        schema = {
            "type": "object",
            "properties": {
                "email": {"type": "string", "format": "email"},
                "website": {"type": "string", "format": "uri"},
                "created_at": {"type": "string", "format": "date"},
            },
        }

        result = generator.generate_from_schema(schema, count=1)
        assert "@" in result["email"]
        assert result["website"].startswith("http")
        assert isinstance(result["created_at"], str)

    def test_generate_integer_with_constraints(self, generator):
        """Test integer generation with min/max constraints."""
        schema = {
            "type": "object",
            "properties": {"score": {"type": "integer", "minimum": 0, "maximum": 100}},
        }

        result = generator.generate_from_schema(schema, count=10)
        for record in result:
            assert 0 <= record["score"] <= 100

    def test_generate_number_with_constraints(self, generator):
        """Test number generation with min/max constraints."""
        schema = {
            "type": "object",
            "properties": {"price": {"type": "number", "minimum": 10.0, "maximum": 50.0}},
        }

        result = generator.generate_from_schema(schema, count=10)
        for record in result:
            assert 10.0 <= record["price"] <= 50.0

    def test_generate_string_with_length_constraints(self, generator):
        """Test string generation with length constraints."""
        schema = {
            "type": "object",
            "properties": {"code": {"type": "string", "minLength": 5, "maxLength": 10}},
        }

        result = generator.generate_from_schema(schema, count=10)
        for record in result:
            assert 5 <= len(record["code"]) <= 10

    def test_generate_array(self, generator):
        """Test array generation."""
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
        """Test nested object generation."""
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string", "format": "email"},
                    },
                }
            },
        }

        result = generator.generate_from_schema(schema, count=1)
        assert isinstance(result["user"], dict)
        assert "name" in result["user"]
        assert "email" in result["user"]
        assert "@" in result["user"]["email"]

    def test_generate_null_type(self, generator):
        """Test null type generation."""
        schema = {
            "type": "object",
            "properties": {"optional_field": {"type": "null"}},
        }

        result = generator.generate_from_schema(schema, count=1)
        assert result["optional_field"] is None

    def test_generate_from_examples(self, generator):
        """Test generating data from examples."""
        examples = [
            {"name": "John", "age": 30, "email": "john@test.com"},
            {"name": "Jane", "age": 25, "email": "jane@test.com"},
            {"name": "Bob", "age": 35, "email": "bob@test.com"},
        ]

        result = generator.generate_from_examples(examples, count=5)
        assert len(result) == 5
        for record in result:
            assert "name" in record
            assert "age" in record
            assert "email" in record
            assert 25 <= record["age"] <= 35  # Should be in similar range
            assert "@" in record["email"]

    def test_generate_from_empty_examples(self, generator):
        """Test with empty examples list."""
        result = generator.generate_from_examples([], count=5)
        assert result == []

    def test_infer_field_types_from_examples(self, generator):
        """Test field type inference from examples."""
        examples = [
            {"name": "John", "age": 30, "score": 85.5, "active": True},
            {"name": "Jane", "age": 25, "score": 92.3, "active": False},
        ]

        field_types = generator._infer_field_types_from_examples(examples)
        assert field_types["name"] == str
        assert field_types["age"] == int
        assert field_types["score"] == float
        assert field_types["active"] == bool

    def test_generate_similar_value_string(self, generator):
        """Test generating similar string values."""
        examples = [{"email": "user@example.com"}]
        value = generator._generate_similar_value("email", examples, str)

        assert isinstance(value, str)
        assert "@" in value

    def test_generate_similar_value_number(self, generator):
        """Test generating similar numeric values."""
        examples = [{"score": 80}, {"score": 90}, {"score": 85}]
        value = generator._generate_similar_value("score", examples, int)

        assert isinstance(value, int)
        assert 80 <= value <= 90

    def test_reproducibility_with_seed(self):
        """Test that seed parameter is accepted and produces output."""
        gen = MockDataGenerator(seed=123)

        schema = {
            "type": "object",
            "properties": {"age": {"type": "integer", "minimum": 18, "maximum": 100}},
        }

        # Should generate valid data with seed
        result = gen.generate_from_schema(schema, count=1)
        assert 18 <= result["age"] <= 100

    def test_generate_by_format_ipv4(self, generator):
        """Test IPv4 generation."""
        value = generator._generate_by_format("ipv4")
        assert isinstance(value, str)
        parts = value.split(".")
        assert len(parts) == 4

    def test_generate_by_format_uuid(self, generator):
        """Test UUID format generation."""
        value = generator._generate_by_format("uuid")
        assert isinstance(value, str)
        assert len(value) == 36  # UUID string length
        assert value.count("-") == 4

    def test_generate_by_format_unknown(self, generator):
        """Test with unknown format."""
        value = generator._generate_by_format("unknown_format")
        assert value is None

    def test_generate_by_pattern_simple(self, generator):
        """Test simple pattern generation."""
        value = generator._generate_by_pattern(r"^\d+$", "code")
        assert isinstance(value, str)
        assert value.isdigit()
