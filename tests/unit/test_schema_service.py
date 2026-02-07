import pytest

from src.bl.builder import SchemaBuilderService


@pytest.fixture
def service():
    return SchemaBuilderService()


def test_simple_string_inference(service):
    data = "hello"
    schema = service.generate_schema(data)
    s = schema.schema_content
    assert s["type"] == "string"
    assert s["minLength"] == 0
    assert s["maxLength"] == 5


def test_email_pattern_inference(service):
    data = "test@example.com"
    schema = service.generate_schema(data)
    s = schema.schema_content
    assert s["type"] == "string"
    assert "pattern" in s
    assert s["pattern"] == r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"


def test_integer_constraints(service):
    data = 10
    schema = service.generate_schema(data)
    s = schema.schema_content
    assert s["type"] == "integer"
    assert s["minimum"] == 0
    assert s["maximum"] == 10


def test_object_no_required(service):
    data = {"name": "Test"}
    schema = service.generate_schema(data)
    s = schema.schema_content
    assert s["type"] == "object"
    assert "required" not in s


def test_list_merging_integers(service):
    data = [5, 15]
    schema = service.generate_schema(data)
    s = schema.schema_content
    assert s["type"] == "array"
    assert s["minItems"] == 0
    assert s["maxItems"] == 2
    assert s["items"]["type"] == "integer"
    assert s["items"]["minimum"] == 0
    assert s["items"]["maximum"] == 15


def test_mixed_array_preserves_object_properties(service):
    data = [{"a": 1}, "string"]
    schema = service.generate_schema(data)
    s = schema.schema_content
    assert s["type"] == "array"
    assert "anyOf" in s["items"]
    found_object = False

    for opt in s["items"]["anyOf"]:
        if opt["type"] == "object":
            assert "a" in opt["properties"]
            found_object = True

    assert found_object, "Object properties were lost in mixed array merge"
