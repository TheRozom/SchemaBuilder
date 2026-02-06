from typing import Any

from src.bl.scoring.engine.scoring_engine import ScoreResult, ScoringEngine
from src.bl.validator import SchemaValidator
from src.core import get_logger
from src.core.config import settings
from src.domain.interfaces import IAIService, ISchemaService
from src.domain.models import (
    ConflictAnalysis,
    SchemaDefinition,
    ValidationResult,
)

logger = get_logger(__name__)


class SchemaBuilderFacade:
    def __init__(self, schema_service: ISchemaService, ai_service: IAIService | None = None):
        self.schema_service = schema_service
        self.ai_service = ai_service
        self.scorer = ScoringEngine()
        self.validator = SchemaValidator()

    async def build_schema_from_list(
        self, data_list: list[Any], enable_ai: bool = None
    ) -> SchemaDefinition:
        if enable_ai is None:
            enable_ai = settings.ENABLE_AI

        logger.info("Building schema from %d items (AI: %s)", len(data_list), enable_ai)

        schema_def, analysis_result = await self.schema_service.generate_schema_from_list(data_list)

        if analysis_result:
            schema_def.analysis = ConflictAnalysis(**analysis_result.summary.model_dump())

        schema_def = await self._enrich_schema(schema_def, data_list, enable_ai=enable_ai)

        logger.info("Schema built with score %d", schema_def.score.overall)

        return schema_def

    def build_schema_from_single(self, data: Any) -> SchemaDefinition:
        logger.info("Building schema from single item")

        schema_def = self.schema_service.generate_schema(data)
        schema_def.score = self.scorer.score(schema_def.schema_content)

        return schema_def

    async def infer_and_score(self, data: Any, enable_ai: bool = None) -> SchemaDefinition:
        if enable_ai is None:
            enable_ai = settings.ENABLE_AI

        logger.info("Inferring and scoring schema (AI: %s)", enable_ai)

        schema_def = self.schema_service.generate_schema(data)
        schema_def = await self._enrich_schema(schema_def, [data], enable_ai=enable_ai)

        return schema_def

    async def _enrich_schema(
        self, schema_def: SchemaDefinition, data: list[Any], enable_ai: bool = False
    ) -> SchemaDefinition:
        score_res = self.scorer.score(schema_def.schema_content)

        if enable_ai and self.ai_service:
            try:
                score_res.ai_score = await self.ai_service.evaluate_schema(
                    schema_def.schema_content
                )
            except Exception as e:
                logger.warning("AI scoring failed: %s", e)

        schema_def.score = score_res

        validation_res = self.validator.validate_data_against_schema(
            schema_def.schema_content, data
        )
        schema_def.validation = ValidationResult(**validation_res.model_dump())

        return schema_def

    def score_schema(self, schema: dict[str, Any]) -> ScoreResult:
        return self.scorer.score(schema)

    def validate_schema(self, schema: dict[str, Any], data: list[Any]) -> ValidationResult:
        result = self.validator.validate_data_against_schema(schema, data)
        return ValidationResult(**result.model_dump())
