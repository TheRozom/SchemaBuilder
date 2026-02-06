from typing import Any, Callable, Dict, Protocol, runtime_checkable

from src.shared.models import SchemaNode


@runtime_checkable
class IRule(Protocol):
    def evaluate(self, schema: Dict[str, Any]) -> float: ...


class BaseRule:
    """Mixin providing shared schema traversal logic for scoring rules."""

    def _traverse_schema(
        self,
        node_dict: Dict[str, Any],
        visit: Callable[[SchemaNode], None],
    ) -> None:
        """Traverse a JSON Schema structure, calling visit() on each node.

        Handles recursion into properties, items, anyOf, oneOf, and allOf.
        Subclasses provide a visit callback to inspect each SchemaNode.

        Args:
            node_dict: The raw schema dict to traverse.
            visit: Callback invoked with a parsed SchemaNode for each node.
        """
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
