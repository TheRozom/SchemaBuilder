"""Functions for analyzing tree structures (counting, path collection)."""

from typing import Any


def collect_paths(
    data: dict[str, Any],
    prefix: str = "",
) -> list[str]:
    """Create a list of all paths in a nested dictionary.

    Paths are in dot notation (e.g., "user.address.city").

    Args:
        data: The dictionary to map
        prefix: Starting path (usually empty)

    Returns:
        List of dot-separated paths like ["person.age", "person.address.city"]
    """
    paths: list[str] = []

    if not isinstance(data, dict):
        return paths

    for key, value in data.items():
        full_path = f"{prefix}.{key}" if prefix else key
        paths.append(full_path)

        if isinstance(value, dict):
            paths.extend(collect_paths(value, full_path))

    return paths


def count_nodes(tree: dict[str, Any] | None) -> int:
    """Count how many keys exist in total (including nested ones).

    Args:
        tree: The dictionary to count

    Returns:
        Total number of keys
    """
    if tree is None:
        return 0

    count = len(tree)

    for subtree in tree.values():
        if subtree is not None and isinstance(subtree, dict):
            count += count_nodes(subtree)

    return count


def flatten(
    tree: dict[str, Any] | None,
    prefix: str = "",
) -> list[str]:
    """Create a sorted list of all paths in a tree.

    Similar to collect_paths but returns sorted results.

    Args:
        tree: The dictionary to flatten
        prefix: Starting path (usually empty)

    Returns:
        Sorted list like ["address.city", "address.street", "name"]
    """
    keys: list[str] = []

    if tree is None:
        return keys

    for key, subtree in tree.items():
        full_key = f"{prefix}.{key}" if prefix else key
        keys.append(full_key)

        if subtree is not None and isinstance(subtree, dict):
            keys.extend(flatten(subtree, full_key))

    return sorted(keys)
