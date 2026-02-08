from typing import Any

from src.core import get_logger
from src.core.service_config import service_config
from src.shared.utils import tree_analysis, tree_operations

logger = get_logger(__name__)


class TreeComparator:
    def contains(self, larger: dict[str, Any], smaller: dict[str, Any]) -> bool:
        return tree_operations.contains(larger, smaller)

    def merge(self, tree1: dict[str, Any], tree2: dict[str, Any]) -> dict[str, Any]:
        logger.debug("Merging two trees")

        return tree_operations.merge(tree1, tree2)

    def flatten(self, tree: dict[str, Any], prefix: str = "") -> list[str]:
        return tree_analysis.flatten(tree, prefix)

    def key_similarity(self, tree_a: dict[str, Any], tree_b: dict[str, Any]) -> float:
        keys_a = set(self.flatten(tree_a))
        keys_b = set(self.flatten(tree_b))

        if not keys_a and not keys_b:
            return 100.0

        if not keys_a or not keys_b:
            return 0.0

        intersection_count = len(keys_a & keys_b)
        smaller_count = min(len(keys_a), len(keys_b))
        return round((intersection_count / smaller_count) * 100, 2)

    def ted_similarity(self, tree_a: dict[str, Any], tree_b: dict[str, Any]) -> float:
        return service_config.ted_calculator.calculate_similarity(tree_a, tree_b)
