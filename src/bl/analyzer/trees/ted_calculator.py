from typing import Any

from zss import Node, simple_distance


class TedCalculator:
    def calculate_similarity(self, tree_a: dict[str, Any], tree_b: dict[str, Any]) -> float:
        if not tree_a and not tree_b:
            return 100.0

        node_a = self._dict_tree_to_zss_node(tree_a, "root")
        node_b = self._dict_tree_to_zss_node(tree_b, "root")

        edit_distance = simple_distance(node_a, node_b)

        max_nodes = max(self._count_nodes(node_a), self._count_nodes(node_b))

        if max_nodes == 0:
            return 100.0

        return (1 - edit_distance / max_nodes) * 100

    def _dict_tree_to_zss_node(self, tree: dict[str, Any], label: str) -> Node:
        node = Node(label)

        for key, value in tree.items():
            if isinstance(value, dict):
                child = self._dict_tree_to_zss_node(value, key)
            else:
                child = Node(key)

            node.addkid(child)

        return node

    def _count_nodes(self, node: Node) -> int:
        count = 1

        for child in Node.get_children(node):
            count += self._count_nodes(child)

        return count
