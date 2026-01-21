from typing import Any, Dict

from src.core import get_logger
from src.shared.utils import TypeChecker, TreeTraversal

logger = get_logger(__name__)


class TreeBuilder:

    def build(self, data: Any) -> Dict[str, Any]:
        logger.debug(
            "Building tree from data type: %s", TypeChecker.get_type_name(data)
        )

        if TypeChecker.is_dict(data):
            tree = {}
            for key, value in data.items():
                if TypeChecker.is_dict(value):
                    tree[key] = self.build(value)
                elif TypeChecker.is_list_of_dicts(value):
                    # Merge all dict structures in the list to capture all keys
                    merged_tree = {}
                    for item in value:
                        if TypeChecker.is_dict(item):
                            item_tree = self.build(item)
                            merged_tree = TreeTraversal.merge_trees(merged_tree, item_tree) or {}
                    tree[f"{key}[]"] = merged_tree
                else:
                    tree[key] = None
            return tree
        return {}

    def count_nodes(self, tree: Dict[str, Any]) -> int:
        return TreeTraversal.count_nodes(tree)
