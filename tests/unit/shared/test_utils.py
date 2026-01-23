"""
Unit tests for TypeChecker and TreeTraversal utilities.
"""

import pytest

from src.shared.utils import TypeChecker, TreeTraversal


class TestTypeChecker:
    """Tests for TypeChecker static methods."""

    # is_dict tests
    def test_is_dict_with_dict_returns_true(self):
        assert TypeChecker.is_dict({}) is True
        assert TypeChecker.is_dict({"key": "value"}) is True

    def test_is_dict_with_non_dict_returns_false(self):
        assert TypeChecker.is_dict([]) is False
        assert TypeChecker.is_dict("string") is False
        assert TypeChecker.is_dict(123) is False
        assert TypeChecker.is_dict(None) is False

    # is_list tests
    def test_is_list_with_list_returns_true(self):
        assert TypeChecker.is_list([]) is True
        assert TypeChecker.is_list([1, 2, 3]) is True

    def test_is_list_with_non_list_returns_false(self):
        assert TypeChecker.is_list({}) is False
        assert TypeChecker.is_list("string") is False
        assert TypeChecker.is_list((1, 2)) is False
        assert TypeChecker.is_list(None) is False

    # is_string tests
    def test_is_string_with_str_returns_true(self):
        assert TypeChecker.is_string("") is True
        assert TypeChecker.is_string("hello") is True

    def test_is_string_with_non_str_returns_false(self):
        assert TypeChecker.is_string(123) is False
        assert TypeChecker.is_string([]) is False
        assert TypeChecker.is_string(None) is False
        assert TypeChecker.is_string(b"bytes") is False

    # is_int tests
    def test_is_int_with_int_returns_true(self):
        assert TypeChecker.is_int(0) is True
        assert TypeChecker.is_int(42) is True
        assert TypeChecker.is_int(-100) is True

    def test_is_int_with_bool_returns_false(self):
        # Bools are subclass of int in Python, but should return False
        assert TypeChecker.is_int(True) is False
        assert TypeChecker.is_int(False) is False

    def test_is_int_with_non_int_returns_false(self):
        assert TypeChecker.is_int(3.14) is False
        assert TypeChecker.is_int("42") is False
        assert TypeChecker.is_int(None) is False

    # is_float tests
    def test_is_float_with_float_returns_true(self):
        assert TypeChecker.is_float(0.0) is True
        assert TypeChecker.is_float(3.14) is True
        assert TypeChecker.is_float(-2.5) is True

    def test_is_float_with_non_float_returns_false(self):
        assert TypeChecker.is_float(42) is False
        assert TypeChecker.is_float("3.14") is False
        assert TypeChecker.is_float(None) is False

    # is_bool tests
    def test_is_bool_with_bool_returns_true(self):
        assert TypeChecker.is_bool(True) is True
        assert TypeChecker.is_bool(False) is True

    def test_is_bool_with_int_1_0_returns_false(self):
        # int 1 and 0 are NOT bools
        assert TypeChecker.is_bool(1) is False
        assert TypeChecker.is_bool(0) is False

    def test_is_bool_with_non_bool_returns_false(self):
        assert TypeChecker.is_bool("true") is False
        assert TypeChecker.is_bool(None) is False
        assert TypeChecker.is_bool([]) is False

    # is_none tests
    def test_is_none_with_none_returns_true(self):
        assert TypeChecker.is_none(None) is True

    def test_is_none_with_non_none_returns_false(self):
        assert TypeChecker.is_none(0) is False
        assert TypeChecker.is_none("") is False
        assert TypeChecker.is_none(False) is False
        assert TypeChecker.is_none([]) is False

    # is_numeric tests
    def test_is_numeric_with_int_returns_true(self):
        assert TypeChecker.is_numeric(42) is True
        assert TypeChecker.is_numeric(-10) is True

    def test_is_numeric_with_float_returns_true(self):
        assert TypeChecker.is_numeric(3.14) is True
        assert TypeChecker.is_numeric(-0.5) is True

    def test_is_numeric_with_non_numeric_returns_false(self):
        assert TypeChecker.is_numeric("42") is False
        assert TypeChecker.is_numeric(True) is False
        assert TypeChecker.is_numeric(None) is False

    # is_primitive tests
    def test_is_primitive_with_primitives_returns_true(self):
        assert TypeChecker.is_primitive("string") is True
        assert TypeChecker.is_primitive(42) is True
        assert TypeChecker.is_primitive(3.14) is True
        assert TypeChecker.is_primitive(True) is True
        assert TypeChecker.is_primitive(None) is True

    def test_is_primitive_with_dict_returns_false(self):
        assert TypeChecker.is_primitive({}) is False
        assert TypeChecker.is_primitive({"key": "value"}) is False

    def test_is_primitive_with_list_returns_false(self):
        assert TypeChecker.is_primitive([]) is False
        assert TypeChecker.is_primitive([1, 2, 3]) is False

    # is_empty_collection tests
    def test_is_empty_collection_with_empty_dict_returns_true(self):
        assert TypeChecker.is_empty_collection({}) is True

    def test_is_empty_collection_with_empty_list_returns_true(self):
        assert TypeChecker.is_empty_collection([]) is True

    def test_is_empty_collection_with_non_empty_returns_false(self):
        assert TypeChecker.is_empty_collection({"a": 1}) is False
        assert TypeChecker.is_empty_collection([1]) is False

    def test_is_empty_collection_with_non_collection_returns_false(self):
        assert TypeChecker.is_empty_collection("") is False
        assert TypeChecker.is_empty_collection(None) is False
        assert TypeChecker.is_empty_collection(0) is False

    # is_list_of_dicts tests
    def test_is_list_of_dicts_with_list_of_dicts_returns_true(self):
        assert TypeChecker.is_list_of_dicts([{"a": 1}]) is True
        assert TypeChecker.is_list_of_dicts([{}, {"b": 2}]) is True

    def test_is_list_of_dicts_with_empty_list_returns_false(self):
        assert TypeChecker.is_list_of_dicts([]) is False

    def test_is_list_of_dicts_with_mixed_list_returns_false(self):
        assert TypeChecker.is_list_of_dicts([{"a": 1}, "string"]) is False
        assert TypeChecker.is_list_of_dicts([{"a": 1}, 42]) is False
        assert TypeChecker.is_list_of_dicts([{"a": 1}, None]) is False

    def test_is_list_of_dicts_with_non_list_returns_false(self):
        assert TypeChecker.is_list_of_dicts({"a": 1}) is False
        assert TypeChecker.is_list_of_dicts("string") is False

    # get_type_name tests
    def test_get_type_name_returns_null_for_none(self):
        assert TypeChecker.get_type_name(None) == "null"

    def test_get_type_name_returns_boolean_for_bool(self):
        assert TypeChecker.get_type_name(True) == "boolean"
        assert TypeChecker.get_type_name(False) == "boolean"

    def test_get_type_name_returns_integer_for_int(self):
        assert TypeChecker.get_type_name(42) == "integer"
        assert TypeChecker.get_type_name(-10) == "integer"

    def test_get_type_name_returns_number_for_float(self):
        assert TypeChecker.get_type_name(3.14) == "number"

    def test_get_type_name_returns_string_for_str(self):
        assert TypeChecker.get_type_name("hello") == "string"

    def test_get_type_name_returns_array_for_list(self):
        assert TypeChecker.get_type_name([1, 2, 3]) == "array"

    def test_get_type_name_returns_object_for_dict(self):
        assert TypeChecker.get_type_name({"key": "value"}) == "object"

    def test_get_type_name_returns_class_name_for_unknown_type(self):
        assert TypeChecker.get_type_name((1, 2)) == "tuple"
        assert TypeChecker.get_type_name({1, 2}) == "set"

    # safe_len tests
    def test_safe_len_returns_length_for_collections(self):
        assert TypeChecker.safe_len([1, 2, 3]) == 3
        assert TypeChecker.safe_len({"a": 1, "b": 2}) == 2
        assert TypeChecker.safe_len("hello") == 5

    def test_safe_len_returns_zero_for_non_sized_types(self):
        assert TypeChecker.safe_len(42) == 0
        assert TypeChecker.safe_len(None) == 0
        assert TypeChecker.safe_len(True) == 0


class TestTreeTraversal:
    """Tests for TreeTraversal static methods."""

    # traverse_dict tests
    def test_traverse_dict_calls_callback_for_each_key(self):
        data = {"a": 1, "b": 2, "c": 3}
        visited = []

        def callback(key, value, depth):
            visited.append((key, value, depth))

        TreeTraversal.traverse_dict(data, callback)

        assert len(visited) == 3
        assert ("a", 1, 0) in visited
        assert ("b", 2, 0) in visited
        assert ("c", 3, 0) in visited

    def test_traverse_dict_traverses_nested_dicts(self):
        data = {"outer": {"inner": "value"}}
        visited = []

        def callback(key, value, depth):
            visited.append((key, depth))

        TreeTraversal.traverse_dict(data, callback)

        assert ("outer", 0) in visited
        assert ("inner", 1) in visited

    def test_traverse_dict_handles_non_dict_input(self):
        visited = []

        def callback(key, value, depth):
            visited.append(key)

        TreeTraversal.traverse_dict("not a dict", callback)
        TreeTraversal.traverse_dict(None, callback)

        assert visited == []

    # traverse_schema_node tests
    def test_traverse_schema_node_traverses_properties(self):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
            },
        }
        visited_depths = []

        def callback(node, depth):
            visited_depths.append(depth)
            return None

        TreeTraversal.traverse_schema_node(schema, callback)

        assert 0 in visited_depths  # root
        assert 1 in visited_depths  # properties

    def test_traverse_schema_node_traverses_items(self):
        schema = {
            "type": "array",
            "items": {"type": "string"},
        }
        visited = []

        def callback(node, depth):
            visited.append((node.get("type"), depth))
            return None

        TreeTraversal.traverse_schema_node(schema, callback)

        assert ("array", 0) in visited
        assert ("string", 1) in visited

    def test_traverse_schema_node_traverses_anyof(self):
        schema = {
            "anyOf": [
                {"type": "string"},
                {"type": "integer"},
            ]
        }
        types_found = []

        def callback(node, depth):
            if "type" in node:
                types_found.append(node["type"])
            return None

        TreeTraversal.traverse_schema_node(schema, callback)

        assert "string" in types_found
        assert "integer" in types_found

    def test_traverse_schema_node_stops_when_callback_returns_false(self):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
            },
        }
        visited = []

        def callback(node, depth):
            visited.append(depth)
            return False  # Stop traversal

        TreeTraversal.traverse_schema_node(schema, callback)

        assert len(visited) == 1
        assert visited[0] == 0

    def test_traverse_schema_node_handles_non_dict_input(self):
        visited = []

        def callback(node, depth):
            visited.append(node)
            return None

        TreeTraversal.traverse_schema_node("not a dict", callback)
        TreeTraversal.traverse_schema_node(None, callback)

        assert visited == []

    # collect_paths tests
    def test_collect_paths_returns_all_paths_with_dot_notation(self):
        data = {
            "user": {
                "name": "John",
                "address": {
                    "city": "NYC",
                },
            },
            "active": True,
        }

        paths = TreeTraversal.collect_paths(data)

        assert "user" in paths
        assert "user.name" in paths
        assert "user.address" in paths
        assert "user.address.city" in paths
        assert "active" in paths

    def test_collect_paths_with_prefix(self):
        data = {"key": "value"}

        paths = TreeTraversal.collect_paths(data, prefix="root")

        assert "root.key" in paths

    def test_collect_paths_returns_empty_for_non_dict(self):
        assert TreeTraversal.collect_paths("not a dict") == []
        assert TreeTraversal.collect_paths(None) == []

    # count_nodes tests
    def test_count_nodes_counts_all_nodes_in_tree(self):
        tree = {
            "a": None,
            "b": {
                "c": None,
                "d": None,
            },
        }

        count = TreeTraversal.count_nodes(tree)

        assert count == 4  # a, b, c, d

    def test_count_nodes_returns_zero_for_none(self):
        assert TreeTraversal.count_nodes(None) == 0

    def test_count_nodes_returns_zero_for_empty_dict(self):
        assert TreeTraversal.count_nodes({}) == 0

    # flatten_tree tests
    def test_flatten_tree_returns_sorted_list_of_full_paths(self):
        tree = {
            "z": None,
            "a": {
                "b": None,
            },
        }

        paths = TreeTraversal.flatten_tree(tree)

        assert paths == ["a", "a.b", "z"]

    def test_flatten_tree_returns_empty_for_none(self):
        assert TreeTraversal.flatten_tree(None) == []

    def test_flatten_tree_with_prefix(self):
        tree = {"key": None}

        paths = TreeTraversal.flatten_tree(tree, prefix="root")

        assert "root.key" in paths

    # tree_contains tests
    def test_tree_contains_returns_true_when_larger_contains_smaller(self):
        larger = {"a": {"b": None, "c": None}, "d": None}
        smaller = {"a": {"b": None}}

        assert TreeTraversal.tree_contains(larger, smaller) is True

    def test_tree_contains_returns_false_when_key_missing(self):
        larger = {"a": None}
        smaller = {"b": None}

        assert TreeTraversal.tree_contains(larger, smaller) is False

    def test_tree_contains_returns_false_when_nested_key_missing(self):
        larger = {"a": {"b": None}}
        smaller = {"a": {"c": None}}

        assert TreeTraversal.tree_contains(larger, smaller) is False

    def test_tree_contains_with_none_smaller_returns_true(self):
        larger = {"a": None}

        assert TreeTraversal.tree_contains(larger, None) is True

    def test_tree_contains_with_none_larger_and_non_none_smaller_returns_false(self):
        smaller = {"a": None}

        assert TreeTraversal.tree_contains(None, smaller) is False

    def test_tree_contains_with_both_none_returns_true(self):
        assert TreeTraversal.tree_contains(None, None) is True

    # merge_trees tests
    def test_merge_trees_combines_two_trees(self):
        tree1 = {"a": None, "b": None}
        tree2 = {"c": None, "d": None}

        merged = TreeTraversal.merge_trees(tree1, tree2)

        assert "a" in merged
        assert "b" in merged
        assert "c" in merged
        assert "d" in merged

    def test_merge_trees_handles_none_tree1(self):
        tree2 = {"a": None}

        merged = TreeTraversal.merge_trees(None, tree2)

        assert merged == tree2

    def test_merge_trees_handles_none_tree2(self):
        tree1 = {"a": None}

        merged = TreeTraversal.merge_trees(tree1, None)

        assert merged == tree1

    def test_merge_trees_handles_both_none(self):
        merged = TreeTraversal.merge_trees(None, None)

        assert merged is None

    def test_merge_trees_recursively_merges_nested_dicts(self):
        tree1 = {"a": {"b": None}}
        tree2 = {"a": {"c": None}}

        merged = TreeTraversal.merge_trees(tree1, tree2)

        assert merged == {"a": {"b": None, "c": None}}

    def test_merge_trees_overwrites_none_with_subtree(self):
        tree1 = {"a": None}
        tree2 = {"a": {"b": None}}

        merged = TreeTraversal.merge_trees(tree1, tree2)

        assert merged == {"a": {"b": None}}

    def test_merge_trees_preserves_subtree_when_other_is_none(self):
        tree1 = {"a": {"b": None}}
        tree2 = {"a": None}

        merged = TreeTraversal.merge_trees(tree1, tree2)

        assert merged == {"a": {"b": None}}

    def test_merge_trees_does_not_modify_original_trees(self):
        tree1 = {"a": None}
        tree2 = {"b": None}
        tree1_copy = dict(tree1)
        tree2_copy = dict(tree2)

        TreeTraversal.merge_trees(tree1, tree2)

        assert tree1 == tree1_copy
        assert tree2 == tree2_copy
