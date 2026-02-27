from fastapi import APIRouter, Depends

from src.api.models import (
    AnalyzeRequest,
    BuildSchemaRequest,
    ReconcileRequest,
    ScoreSchemaRequest,
    ValidateRequest,
    parse_body,
)
from src.bl.analyzer import SchemaAnalyzer
from src.bl.facade import SchemaBuilderFacade
from src.core import get_logger
from src.core.service_factory import get_factory
from src.domain.models import ConflictAnalysis, ReconcileSchemaResponse, SchemaDefinition

logger = get_logger(__name__)

router = APIRouter(prefix="/schemas", tags=["schemas"])


def get_facade() -> SchemaBuilderFacade:
    factory = get_factory()
    return SchemaBuilderFacade(
        schema_service=factory.create_schema_service(),
    )


@router.post("/build", response_model=SchemaDefinition)
@parse_body(BuildSchemaRequest)
async def build_schema(body: BuildSchemaRequest, facade: SchemaBuilderFacade = Depends(get_facade)):
    logger.info("POST /schemas/build - %d items", len(body.data))
    return await facade.build_schema_from_list(body.data)


@router.post("/infer", response_model=SchemaDefinition)
@parse_body()
async def infer_schema_from_data(body, facade: SchemaBuilderFacade = Depends(get_facade)):
    logger.info("POST /schemas/infer")
    return facade.infer_and_score(body)


@router.post("/score")
@parse_body(ScoreSchemaRequest)
async def score_schema(body: ScoreSchemaRequest, facade: SchemaBuilderFacade = Depends(get_facade)):
    logger.info("POST /schemas/score")
    return facade.score_schema(body.json_schema)


@router.post("/analyze", response_model=ConflictAnalysis)
@parse_body(AnalyzeRequest)
def analyze_schema_conflicts(body: AnalyzeRequest):
    logger.info("POST /schemas/analyze - %d items", len(body.data))

    analyzer = SchemaAnalyzer()
    analysis = analyzer.analyze_conflicts(body.data)
    logger.info("Analysis complete: %d unique structures", analysis.unique_structures)

    return ConflictAnalysis(**analysis.summary.model_dump())


@router.post("/validate")
@parse_body(ValidateRequest)
def validate_data(body: ValidateRequest, facade: SchemaBuilderFacade = Depends(get_facade)):
    logger.info("POST /schemas/validate - %d items", len(body.data))

    validation_result = facade.validate_schema(body.json_schema, body.data)
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


@router.post("/reconcile", response_model=ReconcileSchemaResponse)
@parse_body(ReconcileRequest)
async def reconcile_schema(
    body: ReconcileRequest, facade: SchemaBuilderFacade = Depends(get_facade)
):
    logger.info("POST /schemas/reconcile - %d items", len(body.data))
    return await facade.reconcile_schema_with_data(body.json_schema, body.data)
