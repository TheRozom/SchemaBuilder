from typing import Any, Dict

from src.bl.scoring.rules.base import BaseRule
from src.shared.models import SchemaNode, SchemaType


class StrictnessRule(BaseRule):
    def evaluate(self, schema: Dict[str, Any]) -> float:
        total_checks = 0
        passed_checks = 0

        def visit(node: SchemaNode):
            nonlocal total_checks, passed_checks

            if node.type == SchemaType.OBJECT:
                total_checks += 1

                if node.additionalProperties is False:
                    passed_checks += 1

            elif node.type == SchemaType.STRING:
                if node.pattern:
                    total_checks += 1
                    passed_checks += 1

                # Penalize long strings without regex pattern
                if node.maxLength is not None and node.maxLength > 256:
                    total_checks += 1
                    if node.pattern:
                        passed_checks += 1

        self._traverse_schema(schema, visit)

        return passed_checks / total_checks if total_checks > 0 else 1.0
