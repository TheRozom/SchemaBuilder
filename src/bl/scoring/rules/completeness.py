from typing import Any, Dict

from src.bl.scoring.rules.base import IRule
from src.shared.models import SchemaNode, SchemaType


class CompletenessRule(IRule):

    def evaluate(self, schema: Dict[str, Any]) -> float:
        total_checks = 0
        passed_checks = 0

        def traverse(node_dict: Dict[str, Any]):
            if not isinstance(node_dict, dict):
                return

            nonlocal total_checks, passed_checks

            node = SchemaNode(**node_dict)

            if node.type == SchemaType.INTEGER or node.type == SchemaType.NUMBER:
                total_checks += 2
                if node.minimum is not None:
                    passed_checks += 1
                if node.maximum is not None:
                    passed_checks += 1

            elif node.type == SchemaType.STRING:
                total_checks += 2
                if node.minLength is not None:
                    passed_checks += 1
                if node.maxLength is not None:
                    passed_checks += 1

            elif node.type == SchemaType.ARRAY:
                total_checks += 2
                if node.minItems is not None:
                    passed_checks += 1
                if node.maxItems is not None:
                    passed_checks += 1
                if node.items:
                    traverse(node.items)

            elif node.type == SchemaType.OBJECT:
                for prop in node.properties.values():
                    traverse(prop)

        traverse(schema)
        return passed_checks / total_checks if total_checks > 0 else 1.0
