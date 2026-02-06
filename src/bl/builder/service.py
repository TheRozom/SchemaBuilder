from typing import Any, List, Optional, Tuple

from src.core import get_logger
from src.domain.models import SchemaDefinition
from src.shared.exceptions import SchemaBuilderError, SchemaInferenceError
from src.shared.models import AnalysisResult, SchemaNode

from .builders import GroupedSchemaBuilder
from .inferrers import SchemaInferrer
from .normalizers import BoundNormalizer

logger = get_logger(__name__)


class SchemaBuilderService:
    def __init__(
        self,
        inferrer: Optional[SchemaInferrer] = None,
        grouped_builder: Optional[GroupedSchemaBuilder] = None,
    ):
        self.inferrer = inferrer or SchemaInferrer()
        self.grouped_builder = grouped_builder or GroupedSchemaBuilder()
        self.normalizer = BoundNormalizer()
        logger.debug("SchemaBuilderService initialized")

    def generate_schema(self, data: Any) -> SchemaDefinition:
        logger.info("Generating schema from single data sample")

        try:
            self.inferrer.unknown_samples = {}
            schema = self.inferrer.infer(data, path="")

            if self.inferrer.unknown_samples:
                logger.debug(
                    "Found %d paths with unknown patterns (no regex will be added)",
                    len(self.inferrer.unknown_samples),
                )

            if isinstance(schema, SchemaNode):
                self.normalizer.normalize_bounds(schema)
            schema_dict = schema.to_dict() if isinstance(schema, SchemaNode) else schema
            logger.info("Schema generation completed successfully")

            return SchemaDefinition(schema_content=schema_dict)

        except (ValueError, RuntimeError, SchemaBuilderError) as e:
            # Catch expected errors during schema generation
            # Let programming errors (TypeError, AttributeError) propagate for debugging
            logger.error("Schema generation failed: %s", e)
            if isinstance(e, SchemaBuilderError):
                # Re-raise domain exceptions unchanged
                raise
            raise SchemaInferenceError(
                message=f"Failed to generate schema: {e}",
                data_type=type(data).__name__,
            ) from e

    async def generate_schema_from_list(
        self, data_list: List[Any]
    ) -> Tuple[SchemaDefinition, Optional[AnalysisResult]]:
        logger.info("Generating schema from %d data samples", len(data_list))

        try:
            schema_dict, analysis_result = await self.grouped_builder.build_schema(data_list)
            logger.info(
                "Schema generation from list completed, found %d groups",
                analysis_result.unique_structures if analysis_result else 1,
            )

            return SchemaDefinition(schema_content=schema_dict), analysis_result

        except (ValueError, RuntimeError, SchemaBuilderError) as e:
            # Catch expected errors during schema generation
            # Let programming errors (TypeError, AttributeError) propagate for debugging
            logger.error("Schema generation from list failed: %s", e)
            if isinstance(e, SchemaBuilderError):
                # Re-raise domain exceptions unchanged
                raise
            raise SchemaInferenceError(
                message=f"Failed to generate schema from list: {e}",
                details={"item_count": len(data_list)},
            ) from e
