"""Integration tests for generator API endpoints."""

import pytest
from httpx import AsyncClient, ASGITransport
from src.api.main import app

transport = ASGITransport(app=app)


@pytest.mark.asyncio
class TestGeneratorAPI:
    """Integration tests for generator endpoints."""

    async def test_generate_mock_data(self):
        """Test mock data generation endpoint."""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            schema = {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "email": {"type": "string", "format": "email"},
                    "age": {"type": "integer", "minimum": 18, "maximum": 100},
                },
            }

            response = await client.post(
                "/generator/mock-data",
                json={"schema": schema, "count": 10, "use_semantic_hints": True},
            )

            assert response.status_code == 200
            data = response.json()
            assert "count" in data
            assert "data" in data
            assert data["count"] == 10
            assert len(data["data"]) == 10

            # Verify data structure
            for record in data["data"]:
                assert "name" in record
                assert "email" in record
                assert "age" in record
                assert "@" in record["email"]
                assert 18 <= record["age"] <= 100

    async def test_generate_mock_data_empty_schema(self):
        """Test with empty schema."""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/generator/mock-data", json={"schema": {}, "count": 5})

            assert response.status_code == 400

    async def test_generate_from_examples(self):
        """Test generation from examples endpoint."""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            examples = [
                {"name": "John", "age": 30, "city": "New York"},
                {"name": "Jane", "age": 25, "city": "London"},
                {"name": "Bob", "age": 35, "city": "Paris"},
            ]

            response = await client.post(
                "/generator/from-examples", json={"examples": examples, "count": 5}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 5
            assert len(data["data"]) == 5

            # Verify all records have same fields
            for record in data["data"]:
                assert "name" in record
                assert "age" in record
                assert "city" in record

    async def test_generate_from_examples_empty(self):
        """Test with empty examples."""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/generator/from-examples", json={"examples": [], "count": 5}
            )

            assert response.status_code == 400

    async def test_infer_regex_pattern(self):
        """Test regex pattern inference endpoint."""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            examples = ["user@test.com", "admin@example.org", "info@company.net"]

            response = await client.post(
                "/generator/infer-regex", json={"examples": examples, "strict": True}
            )

            assert response.status_code == 200
            data = response.json()
            assert "pattern" in data
            assert "analysis" in data
            assert data["pattern"] is not None
            assert data["analysis"]["likely_type"] == "email"

    async def test_infer_regex_digit_pattern(self):
        """Test regex inference for digit patterns."""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            examples = ["1234", "5678", "9012"]

            response = await client.post(
                "/generator/infer-regex", json={"examples": examples, "strict": True}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["pattern"] == r"^\d{4}$"
            assert data["analysis"]["all_digits"] is True

    async def test_infer_regex_empty_examples(self):
        """Test regex inference with empty examples."""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/generator/infer-regex", json={"examples": [], "strict": True}
            )

            assert response.status_code == 400

    async def test_detect_field_type(self):
        """Test field type detection endpoint."""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/generator/detect-field-type",
                json={
                    "field_name": "user_email",
                    "sample_values": None,
                    "top_suggestions": 3,
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert "field_name" in data
            assert "detected_type" in data
            assert "confidence" in data
            assert "suggestions" in data
            assert len(data["suggestions"]) == 3
            assert data["detected_type"] == "email"
            assert data["confidence"] > 0.5

    async def test_detect_field_type_with_samples(self):
        """Test field type detection with sample values."""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/generator/detect-field-type",
                json={
                    "field_name": "contact_phone",
                    "sample_values": ["123-456-7890", "987-654-3210"],
                    "top_suggestions": 5,
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["field_name"] == "contact_phone"
            assert len(data["suggestions"]) == 5

    async def test_analyze_field(self):
        """Test comprehensive field analysis endpoint."""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/generator/field-analysis",
                json={
                    "field_name": "user_email",
                    "examples": [
                        "john@example.com",
                        "jane@test.org",
                        "bob@company.net",
                    ],
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert "field_name" in data
            assert "semantic" in data
            assert "pattern" in data
            assert data["semantic"]["detected_type"] == "email"
            assert data["pattern"]["generated_regex"] is not None

    async def test_analyze_field_without_examples(self):
        """Test field analysis without examples."""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/generator/field-analysis",
                json={"field_name": "phone_number", "examples": None},
            )

            assert response.status_code == 200
            data = response.json()
            assert "field_name" in data
            assert "semantic" in data
            # Pattern analysis should not be present without examples
            assert "pattern" not in data or data.get("pattern") is None

    async def test_enhance_schema_with_patterns(self):
        """Test schema enhancement with patterns."""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            schema = {
                "type": "object",
                "properties": {
                    "email": {"type": "string"},
                    "zipcode": {"type": "string"},
                },
            }

            examples_by_field = {
                "email": ["user@test.com", "admin@example.org"],
                "zipcode": ["12345", "67890", "11111"],
            }

            response = await client.post(
                "/generator/enhance-schema",
                json={"schema": schema, "examples_by_field": examples_by_field},
            )

            assert response.status_code == 200
            data = response.json()
            assert "schema" in data
            enhanced = data["schema"]
            assert "properties" in enhanced
            assert "email" in enhanced["properties"]
            assert "zipcode" in enhanced["properties"]
            # Check that patterns were added
            assert "pattern" in enhanced["properties"]["email"]
            assert "pattern" in enhanced["properties"]["zipcode"]

    async def test_enhance_schema_empty(self):
        """Test schema enhancement with empty schema."""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/generator/enhance-schema",
                json={"schema": {}, "examples_by_field": {"field": ["value"]}},
            )

            assert response.status_code == 400

    async def test_mock_data_count_limits(self):
        """Test count parameter limits."""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            schema = {
                "type": "object",
                "properties": {"name": {"type": "string"}},
            }

            # Test maximum count
            response = await client.post(
                "/generator/mock-data", json={"schema": schema, "count": 1000}
            )
            assert response.status_code == 200

            # Test minimum count
            response = await client.post(
                "/generator/mock-data", json={"schema": schema, "count": 1}
            )
            assert response.status_code == 200

    async def test_mock_data_complex_schema(self):
        """Test with complex nested schema."""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            schema = {
                "type": "object",
                "properties": {
                    "user": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "email": {"type": "string", "format": "email"},
                            "address": {
                                "type": "object",
                                "properties": {
                                    "street": {"type": "string"},
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
                assert "email" in record["user"]
                assert "address" in record["user"]
                assert 2 <= len(record["tags"]) <= 5

    async def test_semantic_hints_toggle(self):
        """Test semantic hints can be toggled."""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            schema = {
                "type": "object",
                "properties": {
                    "user_email": {"type": "string"},
                },
            }

            # With semantic hints
            response1 = await client.post(
                "/generator/mock-data",
                json={"schema": schema, "count": 1, "use_semantic_hints": True},
            )

            # Without semantic hints
            response2 = await client.post(
                "/generator/mock-data",
                json={"schema": schema, "count": 1, "use_semantic_hints": False},
            )

            assert response1.status_code == 200
            assert response2.status_code == 200

    async def test_regex_strict_vs_flexible(self):
        """Test strict vs flexible regex generation."""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            examples = ["12", "345", "6789"]

            # Strict pattern
            response_strict = await client.post(
                "/generator/infer-regex", json={"examples": examples, "strict": True}
            )

            # Flexible pattern
            response_flexible = await client.post(
                "/generator/infer-regex", json={"examples": examples, "strict": False}
            )

            assert response_strict.status_code == 200
            assert response_flexible.status_code == 200

            strict_pattern = response_strict.json()["pattern"]
            flexible_pattern = response_flexible.json()["pattern"]

            # Patterns should be different
            assert strict_pattern != flexible_pattern
