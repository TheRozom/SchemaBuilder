import pytest

from src.bl.validator import SchemaValidator
from src.shared.exceptions import ValidationError as ValidationException


@pytest.fixture
def validator():
    return SchemaValidator()


@pytest.fixture
def simple_schema():
    return {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "minLength": 1,
                "maxLength": 50,
                "pattern": "^[a-zA-Z]+$",
            },
            "age": {"type": "integer", "minimum": 0, "maximum": 150},
            "email": {"type": "string"},
        },
        "required": ["name", "age"],
        "additionalProperties": False,
    }


@pytest.fixture
def nested_schema():
    return {
        "type": "object",
        "properties": {
            "user": {
                "type": "object",
                "properties": {
                    "profile": {
                        "type": "object",
                        "properties": {
                            "firstName": {"type": "string"},
                            "lastName": {"type": "string"},
                        },
                        "required": ["firstName"],
                    }
                },
                "required": ["profile"],
            }
        },
        "required": ["user"],
    }


@pytest.fixture
def array_schema():
    return {
        "type": "object",
        "properties": {
            "tags": {
                "type": "array",
                "items": {"type": "string", "minLength": 1},
                "minItems": 1,
                "maxItems": 5,
            }
        },
        "required": ["tags"],
    }


class TestValidateDataAgainstSchema:
    def test_valid_data_returns_valid_result(self, validator, simple_schema):
        data = [{"name": "John", "age": 30}]
        result = validator.validate_data_against_schema(simple_schema, data)
        assert result.valid is True
        assert result.total_errors == 0
        assert result.errors == []

    def test_invalid_type_returns_error_with_path(self, validator, simple_schema):
        data = [{"name": "John", "age": "thirty"}]
        result = validator.validate_data_against_schema(simple_schema, data)
        assert result.valid is False
        assert result.total_errors == 1
        assert len(result.errors) == 1
        error = result.errors[0]
        assert error.path == "age"
        assert error.validator == "type"
        assert error.actual_type == "str"
        assert error.expected_type == "integer"

    def test_missing_required_property_returns_error(self, validator, simple_schema):
        data = [{"name": "John"}]
        result = validator.validate_data_against_schema(simple_schema, data)
        assert result.valid is False
        assert result.total_errors == 1
        error = result.errors[0]
        assert error.validator == "required"
        assert "age" in error.message

    def test_value_exceeds_maximum_returns_error(self, validator, simple_schema):
        data = [{"name": "John", "age": 200}]
        result = validator.validate_data_against_schema(simple_schema, data)
        assert result.valid is False
        assert result.total_errors == 1
        error = result.errors[0]
        assert error.path == "age"
        assert error.validator == "maximum"
        assert error.constraint_name == "maximum"
        assert error.constraint_value == 150

    def test_value_below_minimum_returns_error(self, validator, simple_schema):
        data = [{"name": "John", "age": -5}]
        result = validator.validate_data_against_schema(simple_schema, data)
        assert result.valid is False
        assert result.total_errors == 1
        error = result.errors[0]
        assert error.path == "age"
        assert error.validator == "minimum"
        assert error.constraint_name == "minimum"
        assert error.constraint_value == 0

    def test_string_exceeds_max_length_returns_error(self, validator, simple_schema):
        long_name = "A" * 60
        data = [{"name": long_name, "age": 30}]
        result = validator.validate_data_against_schema(simple_schema, data)
        assert result.valid is False
        assert result.total_errors == 1
        error = result.errors[0]
        assert error.path == "name"
        assert error.validator == "maxLength"
        assert error.constraint_name == "maxLength"
        assert error.constraint_value == 50

    def test_string_below_min_length_returns_error(self, validator):
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string", "minLength": 3}},
        }
        data = [{"name": "Jo"}]
        result = validator.validate_data_against_schema(schema, data)
        assert result.valid is False
        assert result.total_errors == 1
        error = result.errors[0]
        assert error.path == "name"
        assert error.validator == "minLength"
        assert error.constraint_name == "minLength"
        assert error.constraint_value == 3

    def test_string_pattern_mismatch_returns_error(self, validator, simple_schema):
        data = [{"name": "John123", "age": 30}]
        result = validator.validate_data_against_schema(simple_schema, data)
        assert result.valid is False
        assert result.total_errors == 1
        error = result.errors[0]
        assert error.path == "name"
        assert error.validator == "pattern"
        assert error.constraint_name == "pattern"
        assert error.constraint_value == "^[a-zA-Z]+$"

    def test_multiple_objects_with_some_invalid_returns_correct_count(
        self, validator, simple_schema
    ):
        data = [
            {"name": "John", "age": 30},
            {"name": "Jane", "age": "young"},
            {"name": "Bob", "age": 25},
            {"name": "A" * 60, "age": 200},
        ]
        result = validator.validate_data_against_schema(simple_schema, data)
        assert result.valid is False
        assert result.total_errors == 3
        indices = [e.object_index for e in result.errors]
        assert 1 in indices
        assert 3 in indices

    def test_nested_object_validation_errors_have_correct_path(self, validator, nested_schema):
        data = [{"user": {"profile": {"lastName": "Doe"}}}]
        result = validator.validate_data_against_schema(nested_schema, data)
        assert result.valid is False
        assert result.total_errors == 1
        error = result.errors[0]
        assert "user" in error.path or "profile" in error.path
        assert error.validator == "required"

    def test_array_item_validation_errors_have_correct_path(self, validator, array_schema):
        data = [{"tags": ["valid", "", "also-valid"]}]
        result = validator.validate_data_against_schema(array_schema, data)
        assert result.valid is False
        assert result.total_errors == 1
        error = result.errors[0]
        assert "tags" in error.path
        assert "1" in error.path

    def test_invalid_schema_raises_exception(self, validator):
        from jsonschema.exceptions import UnknownType

        invalid_schema = {"type": "invalid_type_that_does_not_exist"}
        data = [{"name": "test"}]

        with pytest.raises(UnknownType):
            validator.validate_data_against_schema(invalid_schema, data)

    def test_malformed_schema_raises_validation_exception(self, validator):
        invalid_schema = {
            "$ref": "#/definitions/nonexistent",
            "definitions": {},
        }
        data = [{"name": "test"}]

        try:
            validator.validate_data_against_schema(invalid_schema, data)
            assert True
        except ValidationException as e:
            assert "Invalid schema" in str(e.message)

    def test_empty_data_list_returns_valid(self, validator, simple_schema):
        result = validator.validate_data_against_schema(simple_schema, [])
        assert result.valid is True
        assert result.total_errors == 0

    def test_additional_properties_violation(self, validator, simple_schema):
        data = [{"name": "John", "age": 30, "extra": "field"}]
        result = validator.validate_data_against_schema(simple_schema, data)
        assert result.valid is False
        assert result.total_errors == 1
        error = result.errors[0]
        assert error.validator == "additionalProperties"

    def test_enum_violation_returns_error(self, validator):
        schema = {
            "type": "object",
            "properties": {"status": {"type": "string", "enum": ["active", "inactive", "pending"]}},
        }
        data = [{"status": "unknown"}]
        result = validator.validate_data_against_schema(schema, data)
        assert result.valid is False
        assert result.total_errors == 1
        error = result.errors[0]
        assert error.validator == "enum"
        assert error.allowed_values == ["active", "inactive", "pending"]


class TestValidateSingle:
    def test_validate_single_wraps_validate_data_against_schema(self, validator, simple_schema):
        data = {"name": "John", "age": 30}
        result = validator.validate_single(simple_schema, data)
        assert result.valid is True
        assert result.total_errors == 0

    def test_validate_single_returns_error_for_invalid_data(self, validator, simple_schema):
        data = {"name": "John", "age": "invalid"}
        result = validator.validate_single(simple_schema, data)
        assert result.valid is False
        assert result.total_errors == 1
        assert result.errors[0].object_index == 0

    def test_validate_single_with_nested_object(self, validator, nested_schema):
        data = {"user": {"profile": {"firstName": "John", "lastName": "Doe"}}}
        result = validator.validate_single(nested_schema, data)
        assert result.valid is True
        assert result.total_errors == 0


class TestErrorFormatterOutput:
    def test_error_includes_object_index(self, validator, simple_schema):
        data = [{"name": "Valid", "age": 25}, {"name": "Invalid", "age": "wrong"}]

        result = validator.validate_data_against_schema(simple_schema, data)
        assert len(result.errors) == 1
        assert result.errors[0].object_index == 1

    def test_error_includes_path(self, validator, simple_schema):
        data = [{"name": "John", "age": "invalid"}]
        result = validator.validate_data_against_schema(simple_schema, data)
        error = result.errors[0]
        assert error.path == "age"
        assert isinstance(error.path, str)

    def test_error_includes_message(self, validator, simple_schema):
        data = [{"name": "John", "age": "invalid"}]
        result = validator.validate_data_against_schema(simple_schema, data)
        error = result.errors[0]
        assert error.message is not None
        assert len(error.message) > 0
        assert "integer" in error.message.lower() or "type" in error.message.lower()

    def test_error_includes_fix_suggestion(self, validator, simple_schema):
        data = [{"name": "John", "age": "invalid"}]
        result = validator.validate_data_against_schema(simple_schema, data)
        error = result.errors[0]
        assert error.fix_suggestion is not None
        assert isinstance(error.fix_suggestion, str)

    def test_error_includes_expected_and_actual_type(self, validator, simple_schema):
        data = [{"name": "John", "age": "invalid"}]
        result = validator.validate_data_against_schema(simple_schema, data)
        error = result.errors[0]
        assert error.expected_type == "integer"
        assert error.actual_type == "str"

    def test_error_includes_validator_name(self, validator, simple_schema):
        data = [{"name": "John", "age": 200}]
        result = validator.validate_data_against_schema(simple_schema, data)
        error = result.errors[0]
        assert error.validator == "maximum"

    def test_error_includes_failed_value(self, validator, simple_schema):
        data = [{"name": "John", "age": "not_a_number"}]
        result = validator.validate_data_against_schema(simple_schema, data)
        error = result.errors[0]
        assert error.failed_value is not None
        assert "not_a_number" in error.failed_value

    def test_error_includes_schema_path(self, validator, simple_schema):
        data = [{"name": "John", "age": "invalid"}]
        result = validator.validate_data_against_schema(simple_schema, data)
        error = result.errors[0]
        assert error.schema_path is not None
        assert isinstance(error.schema_path, str)

    def test_error_includes_constraint_info_for_numeric_constraints(self, validator, simple_schema):
        data = [{"name": "John", "age": -10}]
        result = validator.validate_data_against_schema(simple_schema, data)
        error = result.errors[0]
        assert error.constraint_name == "minimum"
        assert error.constraint_value == 0

    def test_failed_value_truncated_for_long_values(self, validator):
        schema = {"type": "integer"}
        long_string = "x" * 200
        data = [long_string]
        result = validator.validate_data_against_schema(schema, data)
        error = result.errors[0]
        assert len(error.failed_value) <= 100


class TestEdgeCases:
    def test_null_value_when_not_allowed(self, validator):
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        data = [{"name": None}]
        result = validator.validate_data_against_schema(schema, data)
        assert result.valid is False

    def test_null_value_when_allowed(self, validator):
        schema = {
            "type": "object",
            "properties": {"name": {"type": ["string", "null"]}},
        }
        data = [{"name": None}]
        result = validator.validate_data_against_schema(schema, data)
        assert result.valid is True

    def test_deeply_nested_error_path(self, validator):
        schema = {
            "type": "object",
            "properties": {
                "level1": {
                    "type": "object",
                    "properties": {
                        "level2": {
                            "type": "object",
                            "properties": {
                                "level3": {
                                    "type": "object",
                                    "properties": {"value": {"type": "integer"}},
                                }
                            },
                        }
                    },
                }
            },
        }
        data = [{"level1": {"level2": {"level3": {"value": "not_int"}}}}]
        result = validator.validate_data_against_schema(schema, data)
        assert result.valid is False
        error = result.errors[0]
        assert "level1" in error.path
        assert "level2" in error.path
        assert "level3" in error.path
        assert "value" in error.path

    def test_multiple_errors_in_single_object(self, validator):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string", "minLength": 5},
                "age": {"type": "integer", "minimum": 18},
            },
            "required": ["name", "age"],
        }
        data = [{"name": "Jo", "age": 10}]
        result = validator.validate_data_against_schema(schema, data)
        assert result.valid is False
        assert result.total_errors == 2
        paths = [e.path for e in result.errors]
        assert "name" in paths
        assert "age" in paths

    def test_array_with_nested_objects_validation(self, validator):
        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"id": {"type": "integer"}},
                "required": ["id"],
            },
        }
        data = [[{"id": 1}, {"id": "two"}, {"id": 3}]]
        result = validator.validate_data_against_schema(schema, data)
        assert result.valid is False
        assert result.total_errors == 1
        error = result.errors[0]
        assert "1" in error.path
        assert "id" in error.path

    def test_validation_result_model_dump(self, validator, simple_schema):
        data = [{"name": "John", "age": "invalid"}]
        result = validator.validate_data_against_schema(simple_schema, data)
        result_dict = result.model_dump()
        assert isinstance(result_dict, dict)
        assert "valid" in result_dict
        assert "total_errors" in result_dict
        assert "errors" in result_dict
        assert result_dict["valid"] is False
        assert result_dict["total_errors"] == 1
