"""Functions for traversing tree-like data structures."""

from collections.abc import Callable
from typing import Any

from src.shared.enums import SchemaKeyword


def traverse_dict(
    data: dict[str, Any],
    callback: Callable[[str, Any, int], None],
    depth: int = 0,
) -> None:
    """Walk through a dictionary, visiting every key-value pair.

    Args:
        data: The dictionary to explore
        callback: Function called for each key-value pair (key, value, depth)
        depth: Current nesting level (0 = top level)
    """
    if not isinstance(data, dict):
        return

    for key, value in data.items():
        callback(key, value, depth)

        if isinstance(value, dict):
            traverse_dict(value, callback, depth + 1)


def traverse_schema_node(
    node: dict[str, Any],
    callback: Callable[[dict[str, Any], int], bool | None],
    depth: int = 0,
) -> None:
    """Walk through a JSON Schema structure.

    Understands JSON Schema keywords like 'properties', 'items', 'anyOf', etc.

    Args:
        node: The schema node to explore
        callback: Function called for each node (node, depth). Return False to stop exploring that branch.
        depth: Current nesting level (0 = top level)
    """
    if not isinstance(node, dict):
        return

    result = callback(node, depth)

    if result is False:
        return

    properties = node.get(SchemaKeyword.PROPERTIES, {})

    for prop_node in properties.values():
        traverse_schema_node(prop_node, callback, depth + 1)

    items = node.get(SchemaKeyword.ITEMS)

    if items and isinstance(items, dict):
        traverse_schema_node(items, callback, depth + 1)

    for keyword in [SchemaKeyword.ANY_OF, SchemaKeyword.ONE_OF, SchemaKeyword.ALL_OF]:
        sub_schemas = node.get(keyword, [])

        for sub_schema in sub_schemas:
            traverse_schema_node(sub_schema, callback, depth + 1)
