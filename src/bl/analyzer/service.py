from typing import Any, List, Optional

from src.core import get_logger
from src.core.service_config import service_config
from src.shared.exceptions import AnalysisError, InputValidationError
from src.shared.models import (
    AnalysisResult,
    AnalysisSummary,
    ConfidenceLevel,
    JsonStructure,
    StructureGroup,
)

logger = get_logger(__name__)


class SchemaAnalyzer:
    def __init__(self):
        self.json_structures: List[JsonStructure] = []
        self.tree_builder = service_config.tree_builder
        self.tree_comparator = service_config.tree_comparator
        self.grouper = service_config.grouper
        self.similarity_calculator = service_config.similarity_calculator
        self.summary_generator = service_config.summary_generator
        logger.debug("SchemaAnalyzer initialized")

    def analyze_conflicts(self, data_list: List[Any]) -> AnalysisResult:
        logger.info("Analyzing conflicts in %d objects", len(data_list))

        empty_result = self._validate_input(data_list)
        if empty_result:
            return empty_result

        try:
            self._build_tree_structures(data_list)

            groups = self.grouper.group_by_containment(self.json_structures)
            logger.debug("Grouped into %d distinct structure groups", len(groups))

            similarity_matrix = self.similarity_calculator.calculate(self.json_structures)

            return self._build_analysis_result(data_list, groups, similarity_matrix)

        except (ValueError, RuntimeError) as e:
            logger.error("Conflict analysis failed: %s", e)
            raise AnalysisError(
                message=f"Failed to analyze conflicts: {e}",
                operation="analyze_conflicts",
                details={"item_count": len(data_list)},
            ) from e

    def _validate_input(self, data_list: List[Any]) -> Optional[AnalysisResult]:
        if not data_list:
            logger.debug("Empty data list provided, returning empty result")
            return AnalysisResult(
                objects_analyzed=0,
                unique_structures=0,
                groups=[],
                similarity_matrix=[],
                summary=AnalysisSummary(
                    total_objects=0,
                    unique_structures=0,
                    should_split_schemas=False,
                    recommendation="No data provided",
                    confidence=ConfidenceLevel.HIGH,
                ),
            )

        non_dict_indices = [i for i, item in enumerate(data_list) if not isinstance(item, dict)]

        if non_dict_indices:
            logger.warning("Non-dict items found at indices: %s", non_dict_indices[:5])
            raise InputValidationError(
                message="All items must be JSON objects (dictionaries)",
                field="data_list",
                details={"invalid_indices": non_dict_indices[:10]},
            )

        return None

    def _build_tree_structures(self, data_list: List[Any]) -> None:
        self.json_structures = []

        for idx, item in enumerate(data_list):
            tree = self.tree_builder.build(item)
            self.json_structures.append(
                JsonStructure(
                    index=idx,
                    tree=tree,
                    key_count=self.tree_builder.count_nodes(tree),
                )
            )

        logger.debug("Built %d tree structures", len(self.json_structures))

    def _create_structure_groups(
        self, groups: List[Any], data_list: List[Any]
    ) -> List[StructureGroup]:
        empty_groups = [i for i, g in enumerate(groups) if not g.indices]
        if empty_groups:
            logger.warning(
                "Skipping %d group(s) with empty indices during analysis",
                len(empty_groups),
            )

        structure_groups = [
            StructureGroup(
                group_id=idx + 1,
                object_indices=group.indices,
                merged_keys=self.tree_comparator.flatten(group.merged_tree),
                key_count=self.tree_builder.count_nodes(group.merged_tree),
                sample=data_list[group.indices[0]],
            )
            for idx, group in enumerate(groups)
            if group.indices
        ]

        return structure_groups

    def _build_analysis_result(
        self,
        data_list: List[Any],
        groups: List[Any],
        similarity_matrix: List[List[float]],
    ) -> AnalysisResult:
        structure_groups = self._create_structure_groups(groups, data_list)

        summary = self.summary_generator.generate(len(data_list), groups, similarity_matrix)

        logger.info(
            "Analysis complete: %d unique structures, recommendation: %s",
            len(groups),
            summary.recommendation[:50],
        )

        return AnalysisResult(
            objects_analyzed=len(data_list),
            unique_structures=len(groups),
            groups=structure_groups,
            similarity_matrix=similarity_matrix,
            summary=summary,
        )
