from src.bl.scoring.rules.base import BaseRule, RuleContext
from src.shared.models import SchemaNode, SchemaType


class CompletenessRule(BaseRule):
    def _evaluate_node(self, node: SchemaNode, context: RuleContext) -> None:
        if node.type == SchemaType.INTEGER or node.type == SchemaType.NUMBER:
            context.add_check(node.minimum is not None)
            context.add_check(node.maximum is not None)

        elif node.type == SchemaType.STRING:
            context.add_check(node.minLength is not None)
            context.add_check(node.maxLength is not None)

        elif node.type == SchemaType.ARRAY:
            context.add_check(node.minItems is not None)
            context.add_check(node.maxItems is not None)
