from typing import Any, Dict, List

from src.core import get_logger
from src.shared.utils import (
    get_type_name,
    is_dict,
    is_list_of_dicts,
    tree_analysis,
    tree_operations,
)

logger = get_logger(__name__)


class TreeBuilder:
    def build(self, data: Any) -> Dict[str, Any]:
        logger.debug("Building tree from data type: %s", get_type_name(data))

        if is_dict(data):
            return self._build_dict_tree(data)

        return {}

    def _build_dict_tree(self, data: Dict[str, Any]) -> Dict[str, Any]:
        tree = {}

        for key, value in data.items():
            if is_dict(value):
                tree[key] = self._build_nested_object(value)

            elif is_list_of_dicts(value):
                tree[f"{key}[]"] = self._build_array_of_objects(value)

            else:
                tree[key] = self._build_leaf_node()

        return tree

    def _build_nested_object(self, value: Dict[str, Any]) -> Dict[str, Any]:
        return self.build(value)

    def _build_array_of_objects(self, items: List[Any]) -> Dict[str, Any]:
        merged_tree = {}

        for item in items:
            if is_dict(item):
                item_tree = self.build(item)
                merged_tree = tree_operations.merge(merged_tree, item_tree) or {}

        return merged_tree

    def _build_leaf_node(self) -> None:
        return None

    def count_nodes(self, tree: Dict[str, Any]) -> int:
        return tree_analysis.count_nodes(tree)
