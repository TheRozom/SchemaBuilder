from typing import Any, Dict

from src.bl.scoring.rules.base import IRule
from src.shared.models import SchemaNode


class AmbiguityRule(IRule):

    def evaluate(self, schema: Dict[str, Any]) -> float:
        total_nodes = 0
        ambiguous_nodes = 0

        def traverse(node_dict: Dict[str, Any]):
            if not isinstance(node_dict, dict):
                return

            nonlocal total_nodes, ambiguous_nodes
            total_nodes += 1

            node = SchemaNode(**node_dict)

            if node.anyOf or node.oneOf:
                ambiguous_nodes += 1

            for v in node.properties.values():
                traverse(v)

            if node.items:
                traverse(node.items)

            for v in node.anyOf:
                traverse(v)

        traverse(schema)

        ratio = ambiguous_nodes / total_nodes if total_nodes > 0 else 0
        return 1.0 - ratio
