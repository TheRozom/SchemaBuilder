from typing import Any

from fastapi import APIRouter, Body, Depends, Request

from src.bl.analyzer import SchemaAnalyzer
from src.bl.facade import SchemaBuilderFacade
from src.core import get_logger
from src.core.service_factory import get_factory
from src.domain.models import ConflictAnalysis, SchemaDefinition
from src.shared import InputValidationError, ValidationException

logger = get_logger(__name__)

router = APIRouter(prefix="/schemas", tags=["schemas"])


def get_facade() -> SchemaBuilderFacade:
    factory = get_factory()
    return SchemaBuilderFacade(
        schema_service=factory.create_schema_service(),
        ai_service=factory.create_ai_service(),
    )


@router.post("/build", response_model=SchemaDefinition)
async def build_schema(
    data: list[Any] = Body(..., description="List of JSON objects to build schema from"),
    facade: SchemaBuilderFacade = Depends(get_facade),
):
    logger.info("POST /schemas/build - %d items", len(data))

    if not data:
        logger.warning("Empty data list provided")
        raise InputValidationError(message="Data list cannot be empty", field="data")

    if not all(isinstance(item, dict) for item in data):
        logger.warning("Non-object items in data list")
        raise InputValidationError(
            message="All items must be JSON objects (not arrays or primitives)",
            field="data",
            expected_type="object",
        )

    return await facade.build_schema_from_list(data)


@router.post("/infer", response_model=SchemaDefinition)
async def infer_schema_from_data(
    request: Request,
    facade: SchemaBuilderFacade = Depends(get_facade),
):
    logger.info("POST /schemas/infer")
    body = await request.body()

    if not body or body == b"":
        data = None

    else:
        import json

        try:
            data = json.loads(body)

        except json.JSONDecodeError as e:
            raise ValidationException(
                message=f"Invalid JSON in request body: {e}",
                details={"error": str(e)},
            ) from e

    return await facade.infer_and_score(data)


@router.post("/score")
async def score_schema(
    json_schema: dict[str, Any] = Body(..., description="JSON Schema to score", alias="schema"),
    facade: SchemaBuilderFacade = Depends(get_facade),
):
    logger.info("POST /schemas/score")

    if not json_schema:
        raise InputValidationError(message="Schema cannot be empty", field="schema")

    return facade.score_schema(json_schema)


@router.post("/analyze", response_model=ConflictAnalysis)
def analyze_schema_conflicts(
    data: list[Any] = Body(..., description="List of JSON objects to analyze for conflicts"),
):
    logger.info("POST /schemas/analyze - %d items", len(data) if isinstance(data, list) else 0)

    if not isinstance(data, list):
        raise InputValidationError(
            message="Data must be a list of JSON objects",
            field="data",
            expected_type="array",
        )

    if len(data) == 0:
        raise InputValidationError(message="Data list cannot be empty", field="data")

    analyzer = SchemaAnalyzer()
    analysis = analyzer.analyze_conflicts(data)
    logger.info("Analysis complete: %d unique structures", analysis.unique_structures)

    return ConflictAnalysis(**analysis.summary.model_dump())


@router.post("/validate")
def validate_data(
    json_schema: dict[str, Any] = Body(
        ..., description="JSON Schema to validate against", alias="schema"
    ),
    data: list[Any] = Body(..., description="List of JSON objects to validate"),
    facade: SchemaBuilderFacade = Depends(get_facade),
):
    logger.info("POST /schemas/validate - %d items", len(data) if data else 0)

    if not json_schema:
        raise InputValidationError(message="Schema cannot be empty", field="schema")

    if not data:
        raise InputValidationError(message="Data list cannot be empty", field="data")

    validation_result = facade.validate_schema(json_schema, data)
    logger.info(
        "Validation complete: valid=%s, errors=%d",
        validation_result.valid,
        validation_result.total_errors,
    )

    errors = validation_result.errors
    if errors and hasattr(errors[0], "model_dump"):
        errors = [error.model_dump() for error in errors]

    return {
        "valid": validation_result.valid,
        "total_errors": validation_result.total_errors,
        "errors": errors,
    }
