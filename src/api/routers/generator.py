from fastapi import APIRouter, Depends

from src.api.models import MockDataRequest, parse_body
from src.bl.generator import MockDataGenerator
from src.core import get_logger
from src.core.service_factory import get_factory

logger = get_logger(__name__)

router = APIRouter(prefix="/generator", tags=["generator"])


def get_mock_generator() -> MockDataGenerator:
    return get_factory().create_mock_generator()


@router.post("/mock-data")
@parse_body(MockDataRequest)
async def generate_mock_data(
    body: MockDataRequest, generator: MockDataGenerator = Depends(get_mock_generator)
):
    logger.info("POST /generator/mock-data - count=%d", body.count)

    result = generator.generate_from_schema(
        body.json_schema,
        count=body.count,
        mode=body.mode,
        min_populated_fields=body.min_populated_fields,
        null_probability=body.null_probability,
    )
    mock_data = [result] if isinstance(result, dict) else result

    logger.info("Generated %d mock records", len(mock_data))

    return {"count": len(mock_data), "data": mock_data}
