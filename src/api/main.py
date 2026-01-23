from typing import Any

from fastapi import FastAPI, Depends, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.core import get_logger
from src.core.config import settings
from src.domain.models import SchemaDefinition, ConflictAnalysis, ValidationResult
from src.domain.interfaces import ISchemaService, IAIService
from src.infrastructure.ai_service import OpenAIService
from src.bl.builder import SchemaBuilderService
from src.bl.scoring.engine.scoring_engine import ScoringEngine
from src.bl.analyzer import SchemaAnalyzer
from src.bl.validator import SchemaValidator
from src.bl.generator import GeneratorService
from src.shared import (
    SchemaBuilderError,
    ValidationException,
    InputValidationError,
)

logger = get_logger(__name__)

app = FastAPI(
    title="Schema Builder API",
    description="Secure JSON Schema generator",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)


@app.exception_handler(SchemaBuilderError)
async def schema_builder_error_handler(_request: Request, exc: SchemaBuilderError) -> JSONResponse:
    logger.error("SchemaBuilderError: %s", exc.message)
    return JSONResponse(
        status_code=400,
        content=exc.to_dict(),
    )


@app.exception_handler(ValidationException)
async def validation_exception_handler(_request: Request, exc: ValidationException) -> JSONResponse:
    logger.error("ValidationException: %s", exc.message)
    return JSONResponse(
        status_code=422,
        content=exc.to_dict(),
    )


def get_ai_service() -> IAIService:
    return OpenAIService()


def get_schema_service(ai: IAIService = Depends(get_ai_service)) -> ISchemaService:
    return SchemaBuilderService(ai_service=ai)


def get_generator_service() -> GeneratorService:
    return GeneratorService()


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}


@app.post("/schemas/build", response_model=SchemaDefinition)
async def build_schema(
    data: list[Any] = Body(..., description="List of JSON objects to build schema from"),
    schema_service: ISchemaService = Depends(get_schema_service),
    ai_service: IAIService = Depends(get_ai_service),
):
    logger.info("POST /schemas/build - %d items", len(data))

    if not data:
        logger.warning("Empty data list provided")
        raise InputValidationError(
            message="Data list cannot be empty",
            field="data",
        )

    if not all(isinstance(item, dict) for item in data):
        logger.warning("Non-object items in data list")
        raise InputValidationError(
            message="All items must be JSON objects (not arrays or primitives)",
            field="data",
            expected_type="object",
        )

    schema_def, analysis_result = await schema_service.generate_schema_from_list(data)

    if analysis_result:
        schema_def.analysis = ConflictAnalysis(**analysis_result.summary.model_dump())

    scorer = ScoringEngine()
    score_res = scorer.score(schema_def.schema_content)

    if settings.ENABLE_AI:
        score_res.ai_score = await ai_service.evaluate_schema(schema_def.schema_content)

    schema_def.score = score_res

    validator = SchemaValidator()
    validation_res = validator.validate_data_against_schema(schema_def.schema_content, data)
    schema_def.validation = ValidationResult(**validation_res.to_dict())

    logger.info("Schema built successfully with score %d", score_res.overall)
    return schema_def


@app.post("/schemas/infer", response_model=SchemaDefinition)
async def infer_schema_from_data(
    request: Request,
    schema_service: ISchemaService = Depends(get_schema_service),
    ai_service: IAIService = Depends(get_ai_service),
):
    logger.info("POST /schemas/infer")

    # Get the raw JSON body to allow null values
    # Handle empty body (from json=None in httpx) as null
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

    schema_def = await schema_service.generate_schema(data)

    scorer = ScoringEngine()
    score_res = scorer.score(schema_def.schema_content)

    if settings.ENABLE_AI:
        score_res.ai_score = await ai_service.evaluate_schema(schema_def.schema_content)

    schema_def.score = score_res

    validator = SchemaValidator()
    data_list = data if isinstance(data, list) else [data]
    validation_res = validator.validate_data_against_schema(schema_def.schema_content, data_list)
    schema_def.validation = ValidationResult(**validation_res.to_dict())

    logger.info("Schema inferred successfully with score %d", score_res.overall)
    return schema_def


@app.post("/schemas/score")
async def score_schema(
    schema: dict[str, Any] = Body(..., description="JSON Schema to score"),
    ai_service: IAIService = Depends(get_ai_service),
):
    logger.info("POST /schemas/score")

    if not schema:
        raise InputValidationError(
            message="Schema cannot be empty",
            field="schema",
        )

    scorer = ScoringEngine()
    score_res = scorer.score(schema)

    if settings.ENABLE_AI:
        score_res.ai_score = await ai_service.evaluate_schema(schema)

    logger.info("Schema scored: %d", score_res.overall)
    return score_res


@app.post("/schemas/analyze", response_model=ConflictAnalysis)
async def analyze_schema_conflicts(
    data: list[Any] = Body(..., description="List of JSON objects to analyze for conflicts")
):
    logger.info("POST /schemas/analyze - %d items", len(data) if isinstance(data, list) else 0)

    if not isinstance(data, list):
        raise InputValidationError(
            message="Data must be a list of JSON objects",
            field="data",
            expected_type="array",
        )

    if len(data) == 0:
        raise InputValidationError(
            message="Data list cannot be empty",
            field="data",
        )

    analyzer = SchemaAnalyzer()
    analysis = analyzer.analyze_conflicts(data)

    logger.info("Analysis complete: %d unique structures", analysis.unique_structures)
    return ConflictAnalysis(**analysis.summary.model_dump())


@app.post("/schemas/validate")
async def validate_data(
    schema: dict[str, Any] = Body(..., description="JSON Schema to validate against"),
    data: list[Any] = Body(..., description="List of JSON objects to validate"),
):
    logger.info("POST /schemas/validate - %d items", len(data) if data else 0)

    if not schema:
        raise InputValidationError(
            message="Schema cannot be empty",
            field="schema",
        )

    if not data:
        raise InputValidationError(
            message="Data list cannot be empty",
            field="data",
        )

    validator = SchemaValidator()
    validation_result = validator.validate_data_against_schema(schema, data)

    logger.info(
        "Validation complete: valid=%s, errors=%d",
        validation_result.valid,
        validation_result.total_errors,
    )

    return {
        "valid": validation_result.valid,
        "total_errors": validation_result.total_errors,
        "errors": [error.model_dump() for error in validation_result.errors],
    }


@app.post("/generator/mock-data")
async def generate_mock_data(
    schema: dict[str, Any] = Body(..., description="JSON Schema to generate data from"),
    count: int = Body(10, description="Number of records to generate", ge=1, le=1000),
    use_semantic_hints: bool = Body(True, description="Use semantic field detection"),
    generator_service: GeneratorService = Depends(get_generator_service),
):
    """Generate mock data from a JSON schema."""
    logger.info("POST /generator/mock-data - count=%d", count)

    if not schema:
        raise InputValidationError(
            message="Schema cannot be empty",
            field="schema",
        )

    mock_data = generator_service.generate_mock_data(
        schema, count=count, use_semantic_hints=use_semantic_hints
    )

    logger.info("Generated %d mock records", len(mock_data))
    return {"count": len(mock_data), "data": mock_data}


@app.post("/generator/from-examples")
async def generate_from_examples(
    examples: list[dict[str, Any]] = Body(..., description="Example records to learn from"),
    count: int = Body(10, description="Number of records to generate", ge=1, le=1000),
    generator_service: GeneratorService = Depends(get_generator_service),
):
    """Generate mock data based on example records."""
    logger.info("POST /generator/from-examples - %d examples, count=%d", len(examples), count)

    if not examples:
        raise InputValidationError(
            message="Examples list cannot be empty",
            field="examples",
        )

    mock_data = generator_service.generate_from_examples(examples, count=count)

    logger.info("Generated %d mock records from examples", len(mock_data))
    return {"count": len(mock_data), "data": mock_data}


@app.post("/generator/infer-regex")
async def infer_regex_pattern(
    examples: list[str] = Body(..., description="Example strings to infer pattern from"),
    strict: bool = Body(True, description="Generate strict or flexible pattern"),
    generator_service: GeneratorService = Depends(get_generator_service),
):
    """Infer regex pattern from example strings without AI."""
    logger.info("POST /generator/infer-regex - %d examples", len(examples))

    if not examples:
        raise InputValidationError(
            message="Examples list cannot be empty",
            field="examples",
        )

    pattern = generator_service.infer_regex_pattern(examples, strict=strict)
    analysis = generator_service.analyze_field_pattern(examples)

    logger.info("Inferred regex pattern: %s", pattern)
    return {
        "pattern": pattern,
        "analysis": analysis,
    }


@app.post("/generator/detect-field-type")
async def detect_field_type(
    field_name: str = Body(..., description="Name of the field"),
    sample_values: list[str] | None = Body(None, description="Optional sample values"),
    top_suggestions: int = Body(3, description="Number of suggestions", ge=1, le=10),
    generator_service: GeneratorService = Depends(get_generator_service),
):
    """Detect semantic field type using embeddings."""
    logger.info("POST /generator/detect-field-type - field=%s", field_name)

    detected_type, confidence = generator_service.detect_field_type(field_name, sample_values)
    suggestions = generator_service.get_field_suggestions(field_name, top_k=top_suggestions)

    logger.info("Detected type: %s (confidence: %.2f)", detected_type, confidence)
    return {
        "field_name": field_name,
        "detected_type": detected_type,
        "confidence": confidence,
        "suggestions": [
            {"type": sug_type, "confidence": sug_conf} for sug_type, sug_conf in suggestions
        ],
    }


@app.post("/generator/field-analysis")
async def analyze_field(
    field_name: str = Body(..., description="Name of the field"),
    examples: list[str] | None = Body(None, description="Optional example values"),
    generator_service: GeneratorService = Depends(get_generator_service),
):
    """Get comprehensive field analysis including semantic type and pattern detection."""
    logger.info("POST /generator/field-analysis - field=%s", field_name)

    report = generator_service.generate_comprehensive_report(field_name, examples)

    logger.info("Field analysis complete for %s", field_name)
    return report


@app.post("/generator/enhance-schema")
async def enhance_schema_with_patterns(
    schema: dict[str, Any] = Body(..., description="JSON Schema to enhance"),
    examples_by_field: dict[str, list[str]] = Body(
        ..., description="Example values for each field"
    ),
    generator_service: GeneratorService = Depends(get_generator_service),
):
    """Enhance JSON schema with inferred regex patterns."""
    logger.info("POST /generator/enhance-schema - %d fields", len(examples_by_field))

    if not schema:
        raise InputValidationError(
            message="Schema cannot be empty",
            field="schema",
        )

    enhanced_schema = generator_service.enhance_schema_with_patterns(schema, examples_by_field)

    logger.info("Schema enhanced with patterns")
    return {"schema": enhanced_schema}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
