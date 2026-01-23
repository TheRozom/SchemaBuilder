import pytest
import re
from src.bl.builder import SchemaBuilderService

from src.bl.builder import SchemaBuilderService
from tests.mocks import MockAIService


@pytest.fixture
def service():
    return SchemaBuilderService(ai_service=MockAIService())


@pytest.mark.asyncio
async def test_simple_string_inference(service):
    data = "hello"
    schema = await service.generate_schema(data)
    s = schema.schema_content
    assert s["type"] == "string"
    assert s["minLength"] == 0
    assert s["maxLength"] == 5


@pytest.mark.asyncio
async def test_email_pattern_inference(service):
    data = "test@example.com"
    schema = await service.generate_schema(data)
    s = schema.schema_content
    assert s["type"] == "string"
    # Check explicitly for pattern regex string (updated to match config pattern)
    assert "pattern" in s
    assert s["pattern"] == r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"


@pytest.mark.asyncio
async def test_integer_constraints(service):
    # Test min/max
    data = 10
    schema = await service.generate_schema(data)
    s = schema.schema_content
    assert s["type"] == "integer"
    assert s["minimum"] == 0
    assert s["maximum"] == 10


@pytest.mark.asyncio
async def test_object_no_required(service):
    data = {"name": "Test"}
    schema = await service.generate_schema(data)
    s = schema.schema_content
    assert s["type"] == "object"
    assert "required" not in s


@pytest.mark.asyncio
async def test_list_merging_integers(service):
    # Merge 5 and 15. Min should be 0, Max should be 15
    data = [5, 15]
    schema = await service.generate_schema(data)
    s = schema.schema_content
    assert s["type"] == "array"
    assert s["minItems"] == 0
    assert s["maxItems"] == 2  # Max length between [5, 15] (len=2) and potentially others?
    # Wait, the test data is `data = [5, 15]`. This is ONE list.
    # Schema inference on `[5, 15]` -> len is 2.
    # The SERVICE inference currently iterates items but the top level IS the list.
    assert s["items"]["type"] == "integer"
    assert s["items"]["minimum"] == 0
    assert s["items"]["maximum"] == 15


@pytest.mark.asyncio
async def test_ai_regex_inference(service):
    # Mock AI expects "ABC" to trigger specific regex
    data = {"code": "ABC-123"}
    schema = await service.generate_schema(data)
    s = schema.schema_content

    # Check that AI logic injected the pattern
    assert "pattern" in s["properties"]["code"]
    assert s["properties"]["code"]["pattern"] == r"^ABC-\d+$"


@pytest.mark.asyncio
async def test_mixed_array_preserves_object_properties(service):
    # Data has object and string
    data = [{"a": 1}, "string"]
    schema = await service.generate_schema(data)
    s = schema.schema_content

    assert s["type"] == "array"
    assert "anyOf" in s["items"]
    # Check that one branch is object WITH properties
    found_object = False
    for opt in s["items"]["anyOf"]:
        if opt["type"] == "object":
            assert "a" in opt["properties"]
            found_object = True
    assert found_object, "Object properties were lost in mixed array merge"
