from typing import Any

from src.bl.analyzer import SchemaAnalyzer
from src.bl.builder.inferrers import SchemaInferrer
from src.bl.builder.mergers import SchemaMerger
from src.bl.builder.normalizers import BoundNormalizer
from src.core import get_logger, load_yaml_config
from src.shared.exceptions import InputValidationError
from src.shared.models import AnalysisResult, SchemaKeyword, SchemaNode

logger = get_logger(__name__)


class GroupedSchemaBuilder:
    def __init__(self) -> None:
        self.config = load_yaml_config("schema_builder.yaml")
        self.analyzer = SchemaAnalyzer()
        self.inferrer = SchemaInferrer()
        self.merger = SchemaMerger()
        self.normalizer = BoundNormalizer()

    async def build_schema(
        self, data_list: list[Any]
    ) -> tuple[dict[str, Any], AnalysisResult | None]:
        if not data_list:
            raise InputValidationError(
                message="Data list cannot be empty",
                field="data_list",
            )

        # Structure analysis requires object inputs; for mixed/primitive lists we
        # can still infer and merge a valid schema directly.
        if not all(isinstance(item, dict) for item in data_list):
            schema = self._build_merged_schema(data_list)
            return schema, None

        if not self.config["schema_building"]["auto_detect_groups"]:
            schema = self._build_merged_schema(data_list)

            return schema, None

        analysis: AnalysisResult = self.analyzer.analyze_conflicts(data_list)
        unique_structures = analysis.unique_structures

        if unique_structures == 1:
            schema = self._build_merged_schema(data_list)

            return schema, analysis

        else:
            strategy = self.config["schema_building"]["strategy"]["multiple_groups"]

            if strategy == SchemaKeyword.ANY_OF:
                schema = self._build_anyof_schema(data_list, analysis)

                return schema, analysis

            else:
                schema = self._build_merged_schema(data_list)

                return schema, analysis

    def _build_merged_schema(self, data_list: list[Any]) -> dict[str, Any]:
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

        if self.inferrer.unknown_samples:
            logger.debug(
                "Found %d paths with unknown patterns (no regex will be added)",
                len(self.inferrer.unknown_samples),
            )

        if merged_schema is None:
            return {}
        if isinstance(merged_schema, SchemaNode):
            self.normalizer.normalize_bounds(merged_schema)
            return merged_schema.to_dict()
        return merged_schema

    def _build_anyof_schema(self, data_list: list[Any], analysis: AnalysisResult) -> dict[str, Any]:
        group_schemas = []

        for group in analysis.groups:
            group_objects = [data_list[idx] for idx in group.object_indices]
            group_schema = self._build_merged_schema(group_objects)
            group_schemas.append(group_schema)

        root_schema = SchemaNode(anyOf=group_schemas)

        return root_schema.to_dict()
