import pytest
from httpx import ASGITransport, AsyncClient

from src.api.main import app

transport = ASGITransport(app=app)


@pytest.mark.asyncio
class TestGeneratorAPI:
    async def test_generate_mock_data(self):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            schema = {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer", "minimum": 18, "maximum": 100},
                },
            }
            response = await client.post(
                "/generator/mock-data",
                json={"schema": schema, "count": 10},
            )
            assert response.status_code == 200
            data = response.json()
            assert "count" in data
            assert "data" in data
            assert data["count"] == 10
            assert len(data["data"]) == 10

            for record in data["data"]:
                assert "name" in record
                assert "age" in record
                assert 18 <= record["age"] <= 100

    async def test_generate_mock_data_empty_schema(self):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/generator/mock-data", json={"schema": {}, "count": 5})
            assert response.status_code == 400

    async def test_mock_data_count_limits(self):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            schema = {
                "type": "object",
                "properties": {"name": {"type": "string"}},
            }
            response = await client.post(
                "/generator/mock-data", json={"schema": schema, "count": 1000}
            )
            assert response.status_code == 200
            response = await client.post(
                "/generator/mock-data", json={"schema": schema, "count": 1}
            )
            assert response.status_code == 200

    async def test_mock_data_with_enum(self):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            schema = {
                "type": "object",
                "properties": {"status": {"type": "string", "enum": ["active", "inactive"]}},
            }
            response = await client.post(
                "/generator/mock-data", json={"schema": schema, "count": 20}
            )
            assert response.status_code == 200
            data = response.json()
            for record in data["data"]:
                assert record["status"] in ["active", "inactive"]

    async def test_mock_data_nested_object(self):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            schema = {
                "type": "object",
                "properties": {
                    "user": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "address": {
                                "type": "object",
                                "properties": {
                                    "city": {"type": "string"},
                                    "zipcode": {"type": "string"},
                                },
                            },
                        },
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 2,
                        "maxItems": 5,
                    },
                },
            }
            response = await client.post(
                "/generator/mock-data", json={"schema": schema, "count": 3}
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data["data"]) == 3

            for record in data["data"]:
                assert "user" in record
                assert "tags" in record
                assert "name" in record["user"]
                assert "address" in record["user"]
                assert 2 <= len(record["tags"]) <= 5

    async def test_mock_data_with_constraints(self):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            schema = {
                "type": "object",
                "properties": {
                    "score": {"type": "integer", "minimum": 0, "maximum": 100},
                    "price": {"type": "number", "minimum": 10.0, "maximum": 50.0},
                    "code": {"type": "string", "minLength": 5, "maxLength": 10},
                },
            }
            response = await client.post(
                "/generator/mock-data", json={"schema": schema, "count": 10}
            )
            assert response.status_code == 200
            data = response.json()

            for record in data["data"]:
                assert 0 <= record["score"] <= 100
                assert 10.0 <= record["price"] <= 50.0
                assert 5 <= len(record["code"]) <= 10

    async def test_mock_data_with_anyof_schema(self):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            schema = {
                "type": "object",
                "properties": {"value": {"anyOf": [{"type": "string"}, {"type": "integer"}]}},
            }
            response = await client.post(
                "/generator/mock-data",
                json={"schema": schema, "count": 10},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 10
            for record in data["data"]:
                assert isinstance(record["value"], (str, int))

    async def test_mock_data_with_top_level_anyof(self):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
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
            response = await client.post(
                "/generator/mock-data",
                json={"schema": schema, "count": 10},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 10
            for record in data["data"]:
                assert "name" in record or "age" in record

    async def test_mock_data_with_null_probability_zero(self):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            schema = {
                "type": "object",
                "properties": {
                    "value": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                },
            }
            response = await client.post(
                "/generator/mock-data",
                json={"schema": schema, "count": 20, "null_probability": 0.0},
            )
            assert response.status_code == 200
            data = response.json()
            assert all(isinstance(record["value"], str) for record in data["data"])

    async def test_mock_data_meaningful_mode_retries_then_fails_when_forced_null(self):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            schema = {
                "type": "object",
                "properties": {
                    "value": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                },
            }
            response = await client.post(
                "/generator/mock-data",
                json={
                    "schema": schema,
                    "count": 1,
                    "mode": "meaningful",
                    "null_probability": 1.0,
                },
            )
            assert response.status_code == 400
