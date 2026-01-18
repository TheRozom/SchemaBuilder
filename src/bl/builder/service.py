from typing import Any, Optional, List, Tuple

from src.core import get_logger
from src.domain.interfaces import ISchemaService, IAIService
from src.domain.models import SchemaDefinition
from src.shared.models import SchemaNode, AnalysisResult
from src.shared.exceptions import SchemaInferenceError, AIServiceError
from .inferrers import SchemaInferrer
from .injectors import RegexInjector
from .builders import GroupedSchemaBuilder

logger = get_logger(__name__)


class SchemaBuilderService(ISchemaService):

    def __init__(self, ai_service: Optional[IAIService] = None):
        self.ai_service = ai_service
        self.inferrer = SchemaInferrer()
        self.injector = RegexInjector()
        self.grouped_builder = GroupedSchemaBuilder(ai_service)
        logger.debug(
            "SchemaBuilderService initialized with AI service: %s",
            ai_service is not None,
        )

    async def generate_schema(self, data: Any) -> SchemaDefinition:
        logger.info("Generating schema from single data sample")

        try:
            self.inferrer.unknown_samples = {}
            schema = self.inferrer.infer(data, path="")

            if self.ai_service and self.inferrer.unknown_samples:
                logger.debug(
                    "Found %d paths with unknown patterns, requesting AI regex generation",
                    len(self.inferrer.unknown_samples),
                )
                for path, samples in self.inferrer.unknown_samples.items():
                    if len(samples) > 0:
                        try:
                            regex = await self.ai_service.generate_regex(samples)
                            if regex:
                                self.injector.inject(schema, path, regex)
                                logger.debug(
                                    "Injected AI-generated regex for path '%s'", path
                                )
                        except Exception as e:
                            logger.warning(
                                "Failed to generate regex for path '%s': %s", path, e
                            )

            schema_dict = schema.to_dict() if isinstance(schema, SchemaNode) else schema
            logger.info("Schema generation completed successfully")
            return SchemaDefinition(schema_content=schema_dict)

        except Exception as e:
            logger.error("Schema generation failed: %s", e)
            raise SchemaInferenceError(
                message=f"Failed to generate schema: {e}",
                data_type=type(data).__name__,
            ) from e

    async def generate_schema_from_list(
        self, data_list: List[Any]
    ) -> Tuple[SchemaDefinition, Optional[AnalysisResult]]:
        logger.info("Generating schema from %d data samples", len(data_list))

        try:
            schema_dict, analysis_result = await self.grouped_builder.build_schema(
                data_list
            )
            logger.info(
                "Schema generation from list completed, found %d groups",
                analysis_result.unique_structures if analysis_result else 1,
            )
            return SchemaDefinition(schema_content=schema_dict), analysis_result

        except Exception as e:
            logger.error("Schema generation from list failed: %s", e)
            raise SchemaInferenceError(
                message=f"Failed to generate schema from list: {e}",
                details={"item_count": len(data_list)},
            ) from e
