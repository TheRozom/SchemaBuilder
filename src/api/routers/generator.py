from typing import Any

from fastapi import APIRouter, Body, Depends

from src.bl.generator import MockDataGenerator
from src.core import get_logger
from src.core.service_factory import get_factory
from src.shared import InputValidationError

logger = get_logger(__name__)

router = APIRouter(prefix="/generator", tags=["generator"])


def get_mock_generator() -> MockDataGenerator:
    return get_factory().create_mock_generator()


@router.post("/mock-data")
async def generate_mock_data(
    json_schema: dict[str, Any] = Body(
        ..., description="JSON Schema to generate data from", alias="schema"
    ),
    count: int = Body(10, description="Number of records to generate", ge=1, le=1000),
    generator: MockDataGenerator = Depends(get_mock_generator),
):
    logger.info("POST /generator/mock-data - count=%d", count)

    if not json_schema:
        raise InputValidationError(
            message="Schema cannot be empty",
            field="schema",
        )

    result = generator.generate_from_schema(json_schema, count=count)
    mock_data = [result] if isinstance(result, dict) else result

    logger.info("Generated %d mock records", len(mock_data))

    return {"count": len(mock_data), "data": mock_data}
