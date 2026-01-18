from typing import Any, Callable, Dict, List, Optional

from src.shared.models import SchemaNode


class TreeTraversal:

    @staticmethod
    def traverse_dict(
        data: Dict[str, Any],
        callback: Callable[[str, Any, int], None],
        depth: int = 0,
    ) -> None:
        if not isinstance(data, dict):
            return

        for key, value in data.items():
            callback(key, value, depth)
            if isinstance(value, dict):
                TreeTraversal.traverse_dict(value, callback, depth + 1)

    @staticmethod
    def traverse_schema_node(
        node: Dict[str, Any],
        callback: Callable[[Dict[str, Any], int], Optional[bool]],
        depth: int = 0,
    ) -> None:
        if not isinstance(node, dict):
            return

        result = callback(node, depth)
        if result is False:
            return

        properties = node.get("properties", {})
        for prop_node in properties.values():
            TreeTraversal.traverse_schema_node(prop_node, callback, depth + 1)

        items = node.get("items")
        if items and isinstance(items, dict):
            TreeTraversal.traverse_schema_node(items, callback, depth + 1)

        for keyword in ["anyOf", "oneOf", "allOf"]:
            sub_schemas = node.get(keyword, [])
            for sub_schema in sub_schemas:
                TreeTraversal.traverse_schema_node(sub_schema, callback, depth + 1)

    @staticmethod
    def collect_paths(
        data: Dict[str, Any],
        prefix: str = "",
    ) -> List[str]:
        paths: List[str] = []

        if not isinstance(data, dict):
            return paths

        for key, value in data.items():
            full_path = f"{prefix}.{key}" if prefix else key
            paths.append(full_path)

            if isinstance(value, dict):
                paths.extend(TreeTraversal.collect_paths(value, full_path))

        return paths

    @staticmethod
    def count_nodes(tree: Optional[Dict[str, Any]]) -> int:
        if tree is None:
            return 0

        count = len(tree)
        for subtree in tree.values():
            if subtree is not None and isinstance(subtree, dict):
                count += TreeTraversal.count_nodes(subtree)

        return count

    @staticmethod
    def flatten_tree(
        tree: Optional[Dict[str, Any]],
        prefix: str = "",
    ) -> List[str]:
        keys: List[str] = []

        if tree is None:
            return keys

        for key, subtree in tree.items():
            full_key = f"{prefix}.{key}" if prefix else key
            keys.append(full_key)

            if subtree is not None and isinstance(subtree, dict):
                keys.extend(TreeTraversal.flatten_tree(subtree, full_key))

        return sorted(keys)

    @staticmethod
    def tree_contains(
        larger: Optional[Dict[str, Any]],
        smaller: Optional[Dict[str, Any]],
    ) -> bool:
        if smaller is None:
            return True
        if larger is None:
            return smaller is None

        for key, subtree in smaller.items():
            if key not in larger:
                return False
            if subtree is not None:
                if larger[key] is None:
                    return False
                if not TreeTraversal.tree_contains(larger[key], subtree):
                    return False

        return True

    @staticmethod
    def merge_trees(
        tree1: Optional[Dict[str, Any]],
        tree2: Optional[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        if tree1 is None:
            return tree2
        if tree2 is None:
            return tree1

        merged = dict(tree1)
        for key, subtree in tree2.items():
            if key in merged:
                if merged[key] is not None and subtree is not None:
                    merged[key] = TreeTraversal.merge_trees(merged[key], subtree)
                elif subtree is not None:
                    merged[key] = subtree
            else:
                merged[key] = subtree

        return merged
