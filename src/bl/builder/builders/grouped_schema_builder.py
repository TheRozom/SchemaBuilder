from typing import Any, List, Dict, Optional, Tuple

from src.core import get_logger, load_yaml_config
from src.shared.models import SchemaNode, AnalysisResult, SchemaKeyword
from src.shared.exceptions import InputValidationError
from src.bl.analyzer import SchemaAnalyzer
from src.bl.builder.inferrers import SchemaInferrer
from src.bl.builder.mergers import SchemaMerger
from src.bl.builder.injectors import RegexInjector
from src.domain.interfaces import IAIService

logger = get_logger(__name__)


class GroupedSchemaBuilder:

    def __init__(self, ai_service: Optional[IAIService] = None) -> None:
        self.ai_service = ai_service
        self.config = load_yaml_config("schema_builder.yaml")
        self.analyzer = SchemaAnalyzer()
        self.inferrer = SchemaInferrer()
        self.merger = SchemaMerger()
        self.injector = RegexInjector()

    async def build_schema(
        self, data_list: List[Any]
    ) -> Tuple[Dict[str, Any], Optional[AnalysisResult]]:
        if not data_list:
            raise InputValidationError(
                message="Data list cannot be empty",
                field="data_list",
            )

        if not self.config["schema_building"]["auto_detect_groups"]:
            schema = await self._build_merged_schema(data_list)
            return schema, None

        analysis: AnalysisResult = self.analyzer.analyze_conflicts(data_list)

        unique_structures = analysis.unique_structures

        if unique_structures == 1:
            schema = await self._build_merged_schema(data_list)
            return schema, analysis
        else:
            strategy = self.config["schema_building"]["strategy"]["multiple_groups"]

            if strategy == SchemaKeyword.ANY_OF:
                schema = await self._build_anyof_schema(data_list, analysis)
                return schema, analysis
            else:
                schema = await self._build_merged_schema(data_list)
                return schema, analysis

    async def _build_merged_schema(self, data_list: List[Any]) -> Dict[str, Any]:
        self.inferrer.unknown_samples = {}
        merged_schema = None

        for item in data_list:
            item_schema = self.inferrer.infer(item, path="")

            if merged_schema is None:
                merged_schema = item_schema
            else:
                first_schema_node = (
                    merged_schema
                    if isinstance(merged_schema, SchemaNode)
                    else SchemaNode(**merged_schema)
                )
                second_schema_node = (
                    item_schema
                    if isinstance(item_schema, SchemaNode)
                    else SchemaNode(**item_schema)
                )
                merged_schema = self.merger.merge(first_schema_node, second_schema_node)

        if self.ai_service and self.inferrer.unknown_samples:
            for path, samples in self.inferrer.unknown_samples.items():
                if len(samples) > 0:
                    regex = await self.ai_service.generate_regex(samples)
                    if regex:
                        self.injector.inject(merged_schema, path, regex)

        return (
            merged_schema.to_dict()
            if isinstance(merged_schema, SchemaNode)
            else merged_schema
        )

    async def _build_anyof_schema(
        self, data_list: List[Any], analysis: AnalysisResult
    ) -> Dict[str, Any]:
        group_schemas = []

        for group in analysis.groups:
            group_objects = [data_list[idx] for idx in group.object_indices]

            group_schema = await self._build_merged_schema(group_objects)
            group_schemas.append(group_schema)

        root_schema = SchemaNode(anyOf=group_schemas)

        return root_schema.to_dict()
