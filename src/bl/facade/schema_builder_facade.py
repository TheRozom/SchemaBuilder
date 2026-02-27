from typing import Any

from src.bl.builder.mergers import SchemaMerger
from src.bl.builder.normalizers import BoundNormalizer
from src.bl.scoring.engine.scoring_engine import ScoreResult, ScoringEngine
from src.bl.validator import SchemaValidator
from src.core import get_logger
from src.domain.interfaces import ISchemaService
from src.domain.models import (
    ConflictAnalysis,
    ReconcileSchemaResponse,
    SchemaDefinition,
    ValidationResult,
)
from src.shared.models import SchemaNode
from src.shared.utils import strip_required_keywords

logger = get_logger(__name__)


class SchemaBuilderFacade:
    def __init__(self, schema_service: ISchemaService):
        self.schema_service = schema_service
        self.scorer = ScoringEngine()
        self.validator = SchemaValidator()
        self.merger = SchemaMerger()
        self.normalizer = BoundNormalizer()

    async def build_schema_from_list(self, data_list: list[Any]) -> SchemaDefinition:
        logger.info("Building schema from %d items", len(data_list))

        schema_def, analysis_result = await self.schema_service.generate_schema_from_list(data_list)

        if analysis_result:
            schema_def.analysis = ConflictAnalysis(**analysis_result.summary.model_dump())

        schema_def = self._enrich_schema(schema_def, data_list)

        logger.info("Schema built with score %d", schema_def.score.overall)

        return schema_def

    def build_schema_from_single(self, data: Any) -> SchemaDefinition:
        logger.info("Building schema from single item")

        schema_def = self.schema_service.generate_schema(data)
        schema_def.score = self.scorer.score(schema_def.schema_content)

        return schema_def

    def infer_and_score(self, data: Any) -> SchemaDefinition:
        logger.info("Inferring and scoring schema")

        schema_def = self.schema_service.generate_schema(data)
        schema_def = self._enrich_schema(schema_def, [data])

        return schema_def

    async def reconcile_schema_with_data(
        self, schema: dict[str, Any], data: list[Any]
    ) -> ReconcileSchemaResponse:
        logger.info("Reconciling provided schema against %d objects", len(data))
        sanitized_schema = strip_required_keywords(schema)

        before_score = self.scorer.score(sanitized_schema)
        before_validation = self.validator.validate_data_against_schema(sanitized_schema, data)

        inferred_schema_def, _analysis_result = await self.schema_service.generate_schema_from_list(
            data
        )
        inferred_schema = inferred_schema_def.schema_content

        merged_schema = self._merge_schema_dicts(sanitized_schema, inferred_schema)

        after_score = self.scorer.score(merged_schema)
        after_validation = self.validator.validate_data_against_schema(merged_schema, data)

        return ReconcileSchemaResponse(
            original_schema=sanitized_schema,
            adjusted_schema=merged_schema,
            score_before=before_score,
            score_after=after_score,
            validation_before=ValidationResult(**before_validation.model_dump()),
            validation_after=ValidationResult(**after_validation.model_dump()),
        )

    def _enrich_schema(self, schema_def: SchemaDefinition, data: list[Any]) -> SchemaDefinition:
        score_res = self.scorer.score(schema_def.schema_content)

        schema_def.score = score_res

        validation_res = self.validator.validate_data_against_schema(
            schema_def.schema_content, data
        )
        schema_def.validation = ValidationResult(**validation_res.model_dump())

        return schema_def

    def score_schema(self, schema: dict[str, Any]) -> ScoreResult:
        return self.scorer.score(strip_required_keywords(schema))

    def validate_schema(self, schema: dict[str, Any], data: list[Any]) -> ValidationResult:
        result = self.validator.validate_data_against_schema(strip_required_keywords(schema), data)
        return ValidationResult(**result.model_dump())

    def _merge_schema_dicts(
        self, base_schema: dict[str, Any], inferred_schema: dict[str, Any]
    ) -> dict[str, Any]:
        base_node = SchemaNode(**base_schema)
        inferred_node = SchemaNode(**inferred_schema)
        merged = self.merger.merge(base_node, inferred_node)
        self.normalizer.normalize_bounds(merged)
        return merged.to_dict()
