from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Protocol, runtime_checkable

from src.shared.models import SchemaNode


@runtime_checkable
class IRule(Protocol):
    def evaluate(self, schema: Dict[str, Any]) -> float: ...


class RuleContext:
    def __init__(self):
        self.total = 0
        self.passed = 0

    def add_check(self, passed: bool = True) -> None:
        self.total += 1
        if passed:
            self.passed += 1

    def get_score(self) -> float:
        return self.passed / self.total if self.total > 0 else 1.0


class BaseRule(ABC):
    def evaluate(self, schema: Dict[str, Any]) -> float:
        context = RuleContext()

        def visit(node: SchemaNode):
            self._evaluate_node(node, context)

        self._traverse_schema(schema, visit)

        return context.get_score()

    @abstractmethod
    def _evaluate_node(self, node: SchemaNode, context: RuleContext) -> None:
        pass

    def _traverse_schema(
        self,
        node_dict: Dict[str, Any],
        visit: Callable[[SchemaNode], None],
    ) -> None:
        if not isinstance(node_dict, dict):
            return

        node = SchemaNode(**node_dict)
        visit(node)

        for prop in node.properties.values():
            self._traverse_schema(prop, visit)

        if node.items:
            self._traverse_schema(node.items, visit)

        for branch in node.anyOf:
            self._traverse_schema(branch, visit)

        for branch in node.oneOf:
            self._traverse_schema(branch, visit)

        for branch in node.allOf:
            self._traverse_schema(branch, visit)
