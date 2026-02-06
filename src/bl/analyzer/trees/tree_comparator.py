from typing import Any

from src.core import get_logger
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
