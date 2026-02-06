from typing import Any, Dict, List

from src.core import get_logger
from src.shared.utils import tree_analysis, tree_operations

logger = get_logger(__name__)


class TreeComparator:
    def contains(self, larger: Dict[str, Any], smaller: Dict[str, Any]) -> bool:
        return tree_operations.contains(larger, smaller)

    def merge(self, tree1: Dict[str, Any], tree2: Dict[str, Any]) -> Dict[str, Any]:
        logger.debug("Merging two trees")

        return tree_operations.merge(tree1, tree2)

    def flatten(self, tree: Dict[str, Any], prefix: str = "") -> List[str]:
        return tree_analysis.flatten(tree, prefix)
