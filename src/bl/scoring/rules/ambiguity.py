from typing import Any

from src.bl.scoring.rules.base import BaseRule, RuleContext
from src.shared.models import SchemaNode


class AmbiguityRuleContext(RuleContext):
    def __init__(self):
        super().__init__()
        self.total_nodes = 0
        self.ambiguous_nodes = 0

    def add_node(self, is_ambiguous: bool = False) -> None:
        self.total_nodes += 1
        if is_ambiguous:
            self.ambiguous_nodes += 1

    def get_score(self) -> float:
        ratio = self.ambiguous_nodes / self.total_nodes if self.total_nodes > 0 else 0
        return 1.0 - ratio


class AmbiguityRule(BaseRule):
    def evaluate(self, schema: dict[str, Any]) -> float:
        context = AmbiguityRuleContext()

        def visit(node: SchemaNode):
            self._evaluate_node(node, context)

        self._traverse_schema(schema, visit)

        return context.get_score()

    def _evaluate_node(self, node: SchemaNode, context: AmbiguityRuleContext) -> None:
        context.add_node(is_ambiguous=bool(node.anyOf or node.oneOf))
