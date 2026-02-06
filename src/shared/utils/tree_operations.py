"""Functions for tree operations like merging and containment checking."""

from typing import Any, Dict, Optional


def contains(
    larger: Optional[Dict[str, Any]],
    smaller: Optional[Dict[str, Any]],
) -> bool:
    """Check if one tree structure is contained within another.

    Returns True if 'larger' has all the keys that 'smaller' has.

    Args:
        larger: The tree that might contain the other
        smaller: The tree to check for

    Returns:
        True if 'smaller' is fully contained in 'larger'
    """
    if smaller is None:
        return True

    if larger is None:
        return smaller is None

    for key, subtree in smaller.items():
        if key not in larger:
            return False

        if subtree is not None:
            if larger[key] is None:
                return False

            if not contains(larger[key], subtree):
                return False

    return True


def merge(
    tree1: Optional[Dict[str, Any]],
    tree2: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """Combine two tree structures into one.

    Recursively merges nested dictionaries. When both trees have the same key,
    tree2's value is preferred (or they are merged if both are dicts).

    Args:
        tree1: First tree
        tree2: Second tree

    Returns:
        A merged tree containing keys from both
    """
    if tree1 is None:
        return tree2

    if tree2 is None:
        return tree1

    merged = dict(tree1)

    for key, subtree in tree2.items():
        if key in merged:
            if merged[key] is not None and subtree is not None:
                merged[key] = merge(merged[key], subtree)

            elif subtree is not None:
                merged[key] = subtree

        else:
            merged[key] = subtree

    return merged
