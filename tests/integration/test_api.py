import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.api.main import app


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health_returns_status_ok(self, client: AsyncClient):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    @pytest.mark.asyncio
    async def test_health_returns_version(self, client: AsyncClient):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert data["version"] == "0.1.0"


class TestInferEndpoint:
    @pytest.mark.asyncio
    async def test_infer_simple_object_returns_object_schema(self, client: AsyncClient):
        data = {"name": "John", "age": 30}
        response = await client.post("/schemas/infer", json=data)
        assert response.status_code == 200
        result = response.json()
        assert result["schema_content"]["type"] == "object"
        assert "properties" in result["schema_content"]
        assert "name" in result["schema_content"]["properties"]
        assert "age" in result["schema_content"]["properties"]

    @pytest.mark.asyncio
    async def test_infer_string_returns_string_schema(self, client: AsyncClient):
        data = "hello world"
        response = await client.post("/schemas/infer", json=data)
        assert response.status_code == 200
        result = response.json()
        assert result["schema_content"]["type"] == "string"

    @pytest.mark.asyncio
    async def test_infer_integer_returns_integer_schema(self, client: AsyncClient):
        data = 42
        response = await client.post("/schemas/infer", json=data)
        assert response.status_code == 200
        result = response.json()
        assert result["schema_content"]["type"] == "integer"

    @pytest.mark.asyncio
    async def test_infer_float_returns_number_schema(self, client: AsyncClient):
        data = 3.14
        response = await client.post("/schemas/infer", json=data)
        assert response.status_code == 200
        result = response.json()
        assert result["schema_content"]["type"] == "number"

    @pytest.mark.asyncio
    async def test_infer_boolean_returns_boolean_schema(self, client: AsyncClient):
        data = True
        response = await client.post("/schemas/infer", json=data)
        assert response.status_code == 200
        result = response.json()
        assert result["schema_content"]["type"] == "boolean"

    @pytest.mark.asyncio
    async def test_infer_array_returns_array_schema(self, client: AsyncClient):
        data = [1, 2, 3]
        response = await client.post("/schemas/infer", json=data)
        assert response.status_code == 200
        result = response.json()
        assert result["schema_content"]["type"] == "array"
        assert "items" in result["schema_content"]

    @pytest.mark.asyncio
    async def test_infer_nested_object_works_correctly(self, client: AsyncClient):
        data = {
            "user": {"name": "John", "address": {"city": "NYC", "zip": "10001"}},
            "active": True,
        }
        response = await client.post("/schemas/infer", json=data)
        assert response.status_code == 200
        result = response.json()
        schema = result["schema_content"]
        assert schema["type"] == "object"
        assert "user" in schema["properties"]
        user_schema = schema["properties"]["user"]
        assert user_schema["type"] == "object"
        assert "address" in user_schema["properties"]

    @pytest.mark.asyncio
    async def test_infer_response_includes_score_with_breakdown(self, client: AsyncClient):
        data = {"name": "John", "age": 30}
        response = await client.post("/schemas/infer", json=data)
        assert response.status_code == 200
        result = response.json()
        assert "score" in result
        assert result["score"] is not None
        assert "total_score" in result["score"]
        assert "breakdown" in result["score"]
        breakdown = result["score"]["breakdown"]
        assert "strictness" in breakdown
        assert "completeness" in breakdown
        assert "ambiguity" in breakdown
        assert "security" in breakdown

    @pytest.mark.asyncio
    async def test_infer_response_includes_validation_result(self, client: AsyncClient):
        data = {"name": "John", "age": 30}
        response = await client.post("/schemas/infer", json=data)
        assert response.status_code == 200
        result = response.json()
        assert "validation" in result
        assert result["validation"] is not None
        assert "valid" in result["validation"]
        assert "total_errors" in result["validation"]
        assert "errors" in result["validation"]

    @pytest.mark.asyncio
    async def test_infer_null_returns_null_schema(self, client: AsyncClient):
        data = None
        response = await client.post("/schemas/infer", json=data)
        assert response.status_code == 200
        result = response.json()
        assert result["schema_content"]["type"] == "null"

    @pytest.mark.asyncio
    async def test_infer_array_of_objects_returns_array_schema(self, client: AsyncClient):
        data = [{"name": "John", "age": 30}, {"name": "Jane", "age": 25}]
        response = await client.post("/schemas/infer", json=data)
        assert response.status_code == 200
        result = response.json()
        assert result["schema_content"]["type"] == "array"
        assert "items" in result["schema_content"]
        items_schema = result["schema_content"]["items"]
        assert items_schema["type"] == "object"


class TestBuildEndpoint:
    @pytest.mark.asyncio
    async def test_build_from_list_returns_merged_schema(self, client: AsyncClient):
        data = [
            {"name": "John", "age": 30},
            {"name": "Jane", "age": 25},
            {"name": "Bob", "age": 35},
        ]
        response = await client.post("/schemas/build", json={"data": data})
        assert response.status_code == 200
        result = response.json()
        assert result["schema_content"]["type"] == "object"
        assert "properties" in result["schema_content"]
        assert "name" in result["schema_content"]["properties"]
        assert "age" in result["schema_content"]["properties"]

    @pytest.mark.asyncio
    async def test_build_empty_list_returns_400_error(self, client: AsyncClient):
        data = []
        response = await client.post("/schemas/build", json={"data": data})
        assert response.status_code == 400
        result = response.json()
        assert "error" in result
        assert "message" in result
        assert "empty" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_build_with_non_objects_returns_400_error(self, client: AsyncClient):
        data = ["string1", "string2"]
        response = await client.post("/schemas/build", json={"data": data})
        assert response.status_code == 400
        result = response.json()
        assert "error" in result
        assert "message" in result

    @pytest.mark.asyncio
    async def test_build_with_mixed_types_returns_400_error(self, client: AsyncClient):
        data = [{"name": "John"}, "not an object", 42]
        response = await client.post("/schemas/build", json={"data": data})
        assert response.status_code == 400
        result = response.json()
        assert "error" in result

    @pytest.mark.asyncio
    async def test_build_response_includes_analysis_for_multiple_structures(
        self, client: AsyncClient
    ):
        data = [
            {"user": {"name": "John"}},
            {"user": {"name": "Jane"}},
            {"product": {"id": 123}},
        ]
        response = await client.post("/schemas/build", json={"data": data})
        assert response.status_code == 200
        result = response.json()
        assert "analysis" in result

    @pytest.mark.asyncio
    async def test_build_response_includes_validation_result(self, client: AsyncClient):
        data = [{"name": "John", "age": 30}, {"name": "Jane", "age": 25}]
        response = await client.post("/schemas/build", json={"data": data})
        assert response.status_code == 200
        result = response.json()
        assert "validation" in result
        assert result["validation"] is not None
        assert "valid" in result["validation"]

    @pytest.mark.asyncio
    async def test_build_response_includes_score(self, client: AsyncClient):
        data = [{"name": "John", "age": 30}, {"name": "Jane", "age": 25}]
        response = await client.post("/schemas/build", json={"data": data})
        assert response.status_code == 200
        result = response.json()
        assert "score" in result
        assert result["score"] is not None
        assert "total_score" in result["score"]
        assert "breakdown" in result["score"]

    @pytest.mark.asyncio
    async def test_build_with_arrays_in_objects_returns_400_error(self, client: AsyncClient):
        data = [[1, 2, 3], [4, 5, 6]]
        response = await client.post("/schemas/build", json={"data": data})
        assert response.status_code == 400
        result = response.json()
        assert "error" in result

    @pytest.mark.asyncio
    async def test_build_with_single_object_works(self, client: AsyncClient):
        data = [{"name": "John", "age": 30}]
        response = await client.post("/schemas/build", json={"data": data})
        assert response.status_code == 200
        result = response.json()
        assert result["schema_content"]["type"] == "object"


class TestAnalyzeEndpoint:
    @pytest.mark.asyncio
    async def test_analyze_identical_objects_returns_one_unique_structure(
        self, client: AsyncClient
    ):
        data = [
            {"name": "John", "age": 30},
            {"name": "Jane", "age": 25},
            {"name": "Bob", "age": 35},
        ]
        response = await client.post("/schemas/analyze", json={"data": data})
        assert response.status_code == 200
        result = response.json()
        assert "unique_structures" in result
        assert result["unique_structures"] == 1

    @pytest.mark.asyncio
    async def test_analyze_different_objects_returns_multiple_structures(self, client: AsyncClient):
        data = [
            {"user": {"name": "John", "email": "john@test.com"}},
            {"user": {"name": "Jane", "email": "jane@test.com"}},
            {"product": {"id": 123, "price": 99.99}},
            {"config": {"version": "1.0", "debug": True}},
        ]
        response = await client.post("/schemas/analyze", json={"data": data})
        assert response.status_code == 200
        result = response.json()
        assert "unique_structures" in result
        assert result["unique_structures"] > 1

    @pytest.mark.asyncio
    async def test_analyze_empty_list_returns_400_error(self, client: AsyncClient):
        data = []
        response = await client.post("/schemas/analyze", json={"data": data})
        assert response.status_code == 400
        result = response.json()
        assert "error" in result
        assert "message" in result

    @pytest.mark.asyncio
    async def test_analyze_non_array_returns_400_error(self, client: AsyncClient):
        response = await client.post("/schemas/analyze", json={"data": {"name": "not an array"}})
        assert response.status_code == 400
        result = response.json()
        assert "error" in result
        assert "message" in result

    @pytest.mark.asyncio
    async def test_analyze_returns_should_split_schemas_recommendation(self, client: AsyncClient):
        data = [{"user": {"name": "John"}}, {"product": {"id": 123}}]
        response = await client.post("/schemas/analyze", json={"data": data})
        assert response.status_code == 200
        result = response.json()
        assert "should_split_schemas" in result
        assert isinstance(result["should_split_schemas"], bool)

    @pytest.mark.asyncio
    async def test_analyze_returns_total_objects_count(self, client: AsyncClient):
        data = [{"name": "John"}, {"name": "Jane"}, {"name": "Bob"}]
        response = await client.post("/schemas/analyze", json={"data": data})
        assert response.status_code == 200
        result = response.json()
        assert "total_objects" in result
        assert result["total_objects"] == 3

    @pytest.mark.asyncio
    async def test_analyze_returns_recommendation_string(self, client: AsyncClient):
        data = [{"user": {"name": "John"}}, {"product": {"id": 123}}]
        response = await client.post("/schemas/analyze", json={"data": data})
        assert response.status_code == 200
        result = response.json()
        assert "recommendation" in result
        assert isinstance(result["recommendation"], str)

    @pytest.mark.asyncio
    async def test_analyze_returns_confidence_level(self, client: AsyncClient):
        data = [{"name": "John"}, {"name": "Jane"}]
        response = await client.post("/schemas/analyze", json={"data": data})
        assert response.status_code == 200
        result = response.json()
        assert "confidence" in result
        assert result["confidence"] in ["low", "medium", "high"]


class TestScoreEndpoint:
    @pytest.mark.asyncio
    async def test_score_valid_schema_returns_score_result(self, client: AsyncClient):
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
        }

        response = await client.post("/schemas/score", json={"schema": schema})
        assert response.status_code == 200
        result = response.json()
        assert "total_score" in result
        assert "breakdown" in result
        assert isinstance(result["total_score"], (int, float))

    @pytest.mark.asyncio
    async def test_score_empty_schema_returns_400_error(self, client: AsyncClient):
        schema = {}
        response = await client.post("/schemas/score", json={"schema": schema})
        assert response.status_code == 400
        result = response.json()
        assert "error" in result
        assert "message" in result

    @pytest.mark.asyncio
    async def test_score_returns_breakdown_with_all_metrics(self, client: AsyncClient):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string", "minLength": 1, "maxLength": 100},
                "age": {"type": "integer", "minimum": 0, "maximum": 150},
            },
            "additionalProperties": False,
        }
        response = await client.post("/schemas/score", json={"schema": schema})
        assert response.status_code == 200
        result = response.json()
        breakdown = result["breakdown"]
        assert "strictness" in breakdown
        assert "completeness" in breakdown
        assert "ambiguity" in breakdown
        assert "security" in breakdown

    @pytest.mark.asyncio
    async def test_score_strict_schema_scores_higher(self, client: AsyncClient):
        strict_schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string", "minLength": 1, "maxLength": 100},
                "age": {"type": "integer", "minimum": 0, "maximum": 150},
            },
            "additionalProperties": False,
        }
        loose_schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
        }

        strict_response = await client.post("/schemas/score", json={"schema": strict_schema})
        loose_response = await client.post("/schemas/score", json={"schema": loose_schema})
        assert strict_response.status_code == 200
        assert loose_response.status_code == 200
        strict_score = strict_response.json()["total_score"]
        loose_score = loose_response.json()["total_score"]
        assert strict_score > loose_score

    @pytest.mark.asyncio
    async def test_score_schema_with_patterns_scores_well(self, client: AsyncClient):
        schema = {
            "type": "object",
            "properties": {
                "email": {
                    "type": "string",
                    "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
                }
            },
        }
        response = await client.post("/schemas/score", json={"schema": schema})
        assert response.status_code == 200
        result = response.json()
        assert result["breakdown"]["strictness"] > 0


class TestValidateEndpoint:
    @pytest.mark.asyncio
    async def test_validate_valid_data_returns_valid_true(self, client: AsyncClient):
        payload = {
            "schema": {
                "type": "object",
                "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
            },
            "data": [{"name": "John", "age": 30}, {"name": "Jane", "age": 25}],
        }
        response = await client.post("/schemas/validate", json=payload)
        assert response.status_code == 200
        result = response.json()
        assert result["valid"] is True
        assert result["total_errors"] == 0
        assert result["errors"] == []

    @pytest.mark.asyncio
    async def test_validate_invalid_data_returns_valid_false_with_errors(self, client: AsyncClient):
        payload = {
            "schema": {
                "type": "object",
                "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
                "required": ["name", "age"],
            },
            "data": [
                {"name": "John"},
                {"name": 123, "age": "not a number"},
            ],
        }
        response = await client.post("/schemas/validate", json=payload)
        assert response.status_code == 200
        result = response.json()
        assert result["valid"] is False
        assert result["total_errors"] > 0
        assert len(result["errors"]) > 0

    @pytest.mark.asyncio
    async def test_validate_empty_schema_returns_400_error(self, client: AsyncClient):
        payload = {"schema": {}, "data": [{"name": "John"}]}
        response = await client.post("/schemas/validate", json=payload)
        assert response.status_code == 400
        result = response.json()
        assert "error" in result
        assert "message" in result

    @pytest.mark.asyncio
    async def test_validate_empty_data_returns_400_error(self, client: AsyncClient):
        payload = {
            "schema": {"type": "object", "properties": {"name": {"type": "string"}}},
            "data": [],
        }
        response = await client.post("/schemas/validate", json=payload)
        assert response.status_code == 400
        result = response.json()
        assert "error" in result
        assert "message" in result

    @pytest.mark.asyncio
    async def test_validate_returns_error_details(self, client: AsyncClient):
        payload = {
            "schema": {
                "type": "object",
                "properties": {"email": {"type": "string", "format": "email"}},
                "required": ["email"],
            },
            "data": [{"email": "not-an-email"}],
        }
        response = await client.post("/schemas/validate", json=payload)
        assert response.status_code == 200
        result = response.json()
        assert "valid" in result
        assert "errors" in result

    @pytest.mark.asyncio
    async def test_validate_with_additional_properties_false(self, client: AsyncClient):
        payload = {
            "schema": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "additionalProperties": False,
            },
            "data": [{"name": "John", "extra": "field"}],
        }
        response = await client.post("/schemas/validate", json=payload)
        assert response.status_code == 200
        result = response.json()
        assert result["valid"] is False
        assert result["total_errors"] > 0

    @pytest.mark.asyncio
    async def test_validate_nested_object_validation(self, client: AsyncClient):
        payload = {
            "schema": {
                "type": "object",
                "properties": {
                    "user": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "age": {"type": "integer"},
                        },
                        "required": ["name"],
                    }
                },
            },
            "data": [
                {"user": {"name": "John", "age": 30}},
                {"user": {"age": 25}},
            ],
        }
        response = await client.post("/schemas/validate", json=payload)
        assert response.status_code == 200
        result = response.json()
        assert result["valid"] is True
        assert result["total_errors"] == 0

    @pytest.mark.asyncio
    async def test_validate_array_items(self, client: AsyncClient):
        payload = {
            "schema": {
                "type": "object",
                "properties": {"tags": {"type": "array", "items": {"type": "string"}}},
            },
            "data": [
                {"tags": ["a", "b", "c"]},
                {"tags": ["x", 123, "z"]},
            ],
        }
        response = await client.post("/schemas/validate", json=payload)
        assert response.status_code == 200
        result = response.json()
        assert result["valid"] is False
        assert result["total_errors"] > 0


class TestReconcileEndpoint:
    @pytest.mark.asyncio
    async def test_reconcile_adjusts_schema_to_fit_data(self, client: AsyncClient):
        payload = {
            "schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "maxLength": 3},
                },
                "required": ["name"],
                "additionalProperties": False,
            },
            "data": [
                {"name": "Elizabeth", "age": 30},
                {"name": "John", "age": 25},
            ],
        }

        response = await client.post("/schemas/reconcile", json=payload)
        assert response.status_code == 200

        result = response.json()
        assert "original_schema" in result
        assert "adjusted_schema" in result
        assert "validation_before" in result
        assert "validation_after" in result
        assert "score_before" in result
        assert "score_after" in result

        assert result["validation_before"]["valid"] is False
        assert result["validation_after"]["valid"] is True

        adjusted_props = result["adjusted_schema"]["properties"]
        assert "age" in adjusted_props
        assert adjusted_props["name"]["maxLength"] >= len("Elizabeth")

    @pytest.mark.asyncio
    async def test_reconcile_empty_data_returns_400_error(self, client: AsyncClient):
        payload = {
            "schema": {"type": "object", "properties": {"name": {"type": "string"}}},
            "data": [],
        }

        response = await client.post("/schemas/reconcile", json=payload)
        assert response.status_code == 400
        result = response.json()
        assert "error" in result
        assert "message" in result

    @pytest.mark.asyncio
    async def test_reconcile_with_non_objects_succeeds(self, client: AsyncClient):
        payload = {
            "schema": {"type": "string", "maxLength": 1},
            "data": ["not-an-object", "ok"],
        }

        response = await client.post("/schemas/reconcile", json=payload)
        assert response.status_code == 200
        result = response.json()
        assert result["validation_before"]["valid"] is False
        assert result["validation_after"]["valid"] is True
        assert result["adjusted_schema"]["type"] == "string"
        assert result["adjusted_schema"]["maxLength"] >= len("not-an-object")


class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_invalid_json_returns_422(self, client: AsyncClient):
        response = await client.post(
            "/schemas/infer",
            content="not valid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_error_response_has_expected_structure(self, client: AsyncClient):
        response = await client.post("/schemas/build", json={"data": []})
        assert response.status_code == 400
        result = response.json()
        assert "error" in result
        assert "message" in result

    @pytest.mark.asyncio
    async def test_score_non_dict_schema_returns_error(self, client: AsyncClient):
        response = await client.post("/schemas/score", json={"schema": "not a schema"})
        assert response.status_code in [400, 422]


class TestEdgeCases:
    @pytest.mark.asyncio
    async def test_infer_empty_object(self, client: AsyncClient):
        data = {}
        response = await client.post("/schemas/infer", json=data)
        assert response.status_code == 200
        result = response.json()
        assert result["schema_content"]["type"] == "object"

    @pytest.mark.asyncio
    async def test_infer_empty_array(self, client: AsyncClient):
        data = []
        response = await client.post("/schemas/infer", json=data)
        assert response.status_code == 200
        result = response.json()
        assert result["schema_content"]["type"] == "array"

    @pytest.mark.asyncio
    async def test_infer_deeply_nested_object(self, client: AsyncClient):
        data = {"level1": {"level2": {"level3": {"level4": {"value": "deep"}}}}}

        response = await client.post("/schemas/infer", json=data)
        assert response.status_code == 200
        result = response.json()
        assert result["schema_content"]["type"] == "object"

    @pytest.mark.asyncio
    async def test_infer_object_with_special_characters_in_keys(self, client: AsyncClient):
        data = {
            "key-with-dash": "value1",
            "key.with.dots": "value2",
            "key_with_underscore": "value3",
        }
        response = await client.post("/schemas/infer", json=data)
        assert response.status_code == 200
        result = response.json()
        assert "key-with-dash" in result["schema_content"]["properties"]

    @pytest.mark.asyncio
    async def test_build_with_optional_fields(self, client: AsyncClient):
        data = [
            {"name": "John", "age": 30, "email": "john@test.com"},
            {"name": "Jane", "age": 25},
            {"name": "Bob"},
        ]
        response = await client.post("/schemas/build", json={"data": data})
        assert response.status_code == 200
        result = response.json()
        props = result["schema_content"]["properties"]
        assert "name" in props
        assert "age" in props
        assert "email" in props

    @pytest.mark.asyncio
    async def test_infer_mixed_array(self, client: AsyncClient):
        data = [1, "two", {"three": 3}, True, None]
        response = await client.post("/schemas/infer", json=data)
        assert response.status_code == 200
        result = response.json()
        assert result["schema_content"]["type"] == "array"

    @pytest.mark.asyncio
    async def test_score_complex_schema(self, client: AsyncClient):
        schema = {
            "type": "object",
            "properties": {
                "id": {"type": "string", "pattern": "^[a-f0-9]{8}$"},
                "name": {"type": "string", "minLength": 1, "maxLength": 255},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 0,
                    "maxItems": 10,
                },
                "metadata": {"type": "object", "additionalProperties": True},
            },
            "required": ["id", "name"],
            "additionalProperties": False,
        }
        response = await client.post("/schemas/score", json={"schema": schema})
        assert response.status_code == 200
        result = response.json()
        assert result["total_score"] > 0
        assert all(
            key in result["breakdown"]
            for key in ["strictness", "completeness", "ambiguity", "security"]
        )

    @pytest.mark.asyncio
    async def test_validate_with_enum_constraint(self, client: AsyncClient):
        payload = {
            "schema": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["active", "inactive", "pending"],
                    }
                },
            },
            "data": [{"status": "active"}, {"status": "invalid_status"}],
        }
        response = await client.post("/schemas/validate", json=payload)
        assert response.status_code == 200
        result = response.json()
        assert result["valid"] is False
        assert result["total_errors"] > 0

    @pytest.mark.asyncio
    async def test_validate_with_minimum_maximum(self, client: AsyncClient):
        payload = {
            "schema": {
                "type": "object",
                "properties": {"age": {"type": "integer", "minimum": 0, "maximum": 150}},
            },
            "data": [
                {"age": 30},
                {"age": -5},
                {"age": 200},
            ],
        }
        response = await client.post("/schemas/validate", json=payload)
        assert response.status_code == 200
        result = response.json()
        assert result["valid"] is False
        assert result["total_errors"] >= 2

    @pytest.mark.asyncio
    async def test_analyze_single_object(self, client: AsyncClient):
        data = [{"name": "John", "age": 30}]
        response = await client.post("/schemas/analyze", json={"data": data})
        assert response.status_code == 200
        result = response.json()
        assert result["total_objects"] == 1
        assert result["unique_structures"] == 1
