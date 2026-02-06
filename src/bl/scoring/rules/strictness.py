from src.bl.scoring.rules.base import BaseRule, RuleContext
from src.shared.models import SchemaNode, SchemaType


class StrictnessRule(BaseRule):
    def _evaluate_node(self, node: SchemaNode, context: RuleContext) -> None:
        if node.type == SchemaType.OBJECT:
            context.add_check(node.additionalProperties is False)

        elif node.type == SchemaType.STRING:
            if node.pattern:
                context.add_check(True)

            if node.maxLength is not None and node.maxLength > 256:
                context.add_check(node.pattern is not None)
