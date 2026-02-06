from typing import Any, Dict

from src.bl.scoring.rules.base import BaseRule
from src.shared.models import SchemaNode


class AmbiguityRule(BaseRule):
    def evaluate(self, schema: Dict[str, Any]) -> float:
        total_nodes = 0
        ambiguous_nodes = 0

        def visit(node: SchemaNode):
            nonlocal total_nodes, ambiguous_nodes
            total_nodes += 1

            if node.anyOf or node.oneOf:
                ambiguous_nodes += 1

        self._traverse_schema(schema, visit)
        ratio = ambiguous_nodes / total_nodes if total_nodes > 0 else 0

        return 1.0 - ratio
