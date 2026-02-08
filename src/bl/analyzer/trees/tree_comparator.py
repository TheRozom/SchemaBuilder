from typing import Any

from src.core import get_logger
from src.core.config_loader import load_yaml_config
from src.core.service_config import service_config
from src.shared.utils import tree_analysis, tree_operations

logger = get_logger(__name__)

DEFAULT_DEPTH_DECAY = 0.5


class TreeComparator:
    def __init__(self) -> None:
        config = load_yaml_config("grouper.yaml")
        grouping_config = config.get("grouping", {})
        self.depth_decay = grouping_config.get("depth_decay", DEFAULT_DEPTH_DECAY)

    def contains(self, larger: dict[str, Any], smaller: dict[str, Any]) -> bool:
        return tree_operations.contains(larger, smaller)

    def merge(self, tree1: dict[str, Any], tree2: dict[str, Any]) -> dict[str, Any]:
        logger.debug("Merging two trees")

        return tree_operations.merge(tree1, tree2)

    def flatten(self, tree: dict[str, Any], prefix: str = "") -> list[str]:
        return tree_analysis.flatten(tree, prefix)

    def _key_weight(self, key_path: str) -> float:
        depth = key_path.count(".") + 1
        return self.depth_decay ** (depth - 1)

    def key_similarity(self, tree_a: dict[str, Any], tree_b: dict[str, Any]) -> float:
        keys_a = set(self.flatten(tree_a))
        keys_b = set(self.flatten(tree_b))

        if not keys_a and not keys_b:
            return 100.0

        if not keys_a or not keys_b:
            return 0.0

        intersection = keys_a & keys_b
        weighted_intersection = sum(self._key_weight(k) for k in intersection)
        weighted_a = sum(self._key_weight(k) for k in keys_a)
        weighted_b = sum(self._key_weight(k) for k in keys_b)
        smaller_weighted = min(weighted_a, weighted_b)
        return round((weighted_intersection / smaller_weighted) * 100, 2)

    def ted_similarity(self, tree_a: dict[str, Any], tree_b: dict[str, Any]) -> float:
        return service_config.ted_calculator.calculate_similarity(tree_a, tree_b)
