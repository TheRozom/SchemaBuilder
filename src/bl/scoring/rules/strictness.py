from typing import Any, Dict

from src.bl.scoring.rules.base import IRule
from src.shared.models import SchemaNode, SchemaType


class StrictnessRule(IRule):

    def evaluate(self, schema: Dict[str, Any]) -> float:
        total_checks = 0
        passed_checks = 0

        def traverse(node_dict: Dict[str, Any]):
            if not isinstance(node_dict, dict):
                return

            nonlocal total_checks, passed_checks

            node = SchemaNode(**node_dict)

            if node.type == SchemaType.OBJECT:
                total_checks += 1
                if node.additionalProperties is False:
                    passed_checks += 1
                for prop in node.properties.values():
                    traverse(prop)

            elif node.type == SchemaType.STRING:
                if node.pattern:
                    total_checks += 1
                    passed_checks += 1

            elif node.type == SchemaType.ARRAY:
                if node.items:
                    traverse(node.items)

            # Traverse composition keywords (anyOf, oneOf, allOf)
            for branch in node.anyOf:
                traverse(branch)
            for branch in node.oneOf:
                traverse(branch)
            for branch in node.allOf:
                traverse(branch)

        traverse(schema)
        return passed_checks / total_checks if total_checks > 0 else 1.0
