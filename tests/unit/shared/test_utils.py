from src.shared.utils import (
    get_type_name,
    is_bool,
    is_dict,
    is_empty_collection,
    is_float,
    is_int,
    is_list,
    is_list_of_dicts,
    is_none,
    is_numeric,
    is_primitive,
    is_string,
    safe_len,
    tree_analysis,
    tree_operations,
    tree_traversal,
)


class TestTypeChecker:
    def test_is_dict_with_dict_returns_true(self):
        assert is_dict({}) is True
        assert is_dict({"key": "value"}) is True

    def test_is_dict_with_non_dict_returns_false(self):
        assert is_dict([]) is False
        assert is_dict("string") is False
        assert is_dict(123) is False
        assert is_dict(None) is False

    def test_is_list_with_list_returns_true(self):
        assert is_list([]) is True
        assert is_list([1, 2, 3]) is True

    def test_is_list_with_non_list_returns_false(self):
        assert is_list({}) is False
        assert is_list("string") is False
        assert is_list((1, 2)) is False
        assert is_list(None) is False

    def test_is_string_with_str_returns_true(self):
        assert is_string("") is True
        assert is_string("hello") is True

    def test_is_string_with_non_str_returns_false(self):
        assert is_string(123) is False
        assert is_string([]) is False
        assert is_string(None) is False
        assert is_string(b"bytes") is False

    def test_is_int_with_int_returns_true(self):
        assert is_int(0) is True
        assert is_int(42) is True
        assert is_int(-100) is True

    def test_is_int_with_bool_returns_false(self):
        assert is_int(True) is False
        assert is_int(False) is False

    def test_is_int_with_non_int_returns_false(self):
        assert is_int(3.14) is False
        assert is_int("42") is False
        assert is_int(None) is False

    def test_is_float_with_float_returns_true(self):
        assert is_float(0.0) is True
        assert is_float(3.14) is True
        assert is_float(-2.5) is True

    def test_is_float_with_non_float_returns_false(self):
        assert is_float(42) is False
        assert is_float("3.14") is False
        assert is_float(None) is False

    def test_is_bool_with_bool_returns_true(self):
        assert is_bool(True) is True
        assert is_bool(False) is True

    def test_is_bool_with_int_1_0_returns_false(self):
        assert is_bool(1) is False
        assert is_bool(0) is False

    def test_is_bool_with_non_bool_returns_false(self):
        assert is_bool("true") is False
        assert is_bool(None) is False
        assert is_bool([]) is False

    def test_is_none_with_none_returns_true(self):
        assert is_none(None) is True

    def test_is_none_with_non_none_returns_false(self):
        assert is_none(0) is False
        assert is_none("") is False
        assert is_none(False) is False
        assert is_none([]) is False

    def test_is_numeric_with_int_returns_true(self):
        assert is_numeric(42) is True
        assert is_numeric(-10) is True

    def test_is_numeric_with_float_returns_true(self):
        assert is_numeric(3.14) is True
        assert is_numeric(-0.5) is True

    def test_is_numeric_with_non_numeric_returns_false(self):
        assert is_numeric("42") is False
        assert is_numeric(True) is False
        assert is_numeric(None) is False

    def test_is_primitive_with_primitives_returns_true(self):
        assert is_primitive("string") is True
        assert is_primitive(42) is True
        assert is_primitive(3.14) is True
        assert is_primitive(True) is True
        assert is_primitive(None) is True

    def test_is_primitive_with_dict_returns_false(self):
        assert is_primitive({}) is False
        assert is_primitive({"key": "value"}) is False

    def test_is_primitive_with_list_returns_false(self):
        assert is_primitive([]) is False
        assert is_primitive([1, 2, 3]) is False

    def test_is_empty_collection_with_empty_dict_returns_true(self):
        assert is_empty_collection({}) is True

    def test_is_empty_collection_with_empty_list_returns_true(self):
        assert is_empty_collection([]) is True

    def test_is_empty_collection_with_non_empty_returns_false(self):
        assert is_empty_collection({"a": 1}) is False
        assert is_empty_collection([1]) is False

    def test_is_empty_collection_with_non_collection_returns_false(self):
        assert is_empty_collection("") is False
        assert is_empty_collection(None) is False
        assert is_empty_collection(0) is False

    def test_is_list_of_dicts_with_list_of_dicts_returns_true(self):
        assert is_list_of_dicts([{"a": 1}]) is True
        assert is_list_of_dicts([{}, {"b": 2}]) is True

    def test_is_list_of_dicts_with_empty_list_returns_false(self):
        assert is_list_of_dicts([]) is False

    def test_is_list_of_dicts_with_mixed_list_returns_false(self):
        assert is_list_of_dicts([{"a": 1}, "string"]) is False
        assert is_list_of_dicts([{"a": 1}, 42]) is False
        assert is_list_of_dicts([{"a": 1}, None]) is False

    def test_is_list_of_dicts_with_non_list_returns_false(self):
        assert is_list_of_dicts({"a": 1}) is False
        assert is_list_of_dicts("string") is False

    def test_get_type_name_returns_null_for_none(self):
        assert get_type_name(None) == "null"

    def test_get_type_name_returns_boolean_for_bool(self):
        assert get_type_name(True) == "boolean"
        assert get_type_name(False) == "boolean"

    def test_get_type_name_returns_integer_for_int(self):
        assert get_type_name(42) == "integer"
        assert get_type_name(-10) == "integer"

    def test_get_type_name_returns_number_for_float(self):
        assert get_type_name(3.14) == "number"

    def test_get_type_name_returns_string_for_str(self):
        assert get_type_name("hello") == "string"

    def test_get_type_name_returns_array_for_list(self):
        assert get_type_name([1, 2, 3]) == "array"

    def test_get_type_name_returns_object_for_dict(self):
        assert get_type_name({"key": "value"}) == "object"

    def test_get_type_name_returns_class_name_for_unknown_type(self):
        assert get_type_name((1, 2)) == "tuple"
        assert get_type_name({1, 2}) == "set"

    def test_safe_len_returns_length_for_collections(self):
        assert safe_len([1, 2, 3]) == 3
        assert safe_len({"a": 1, "b": 2}) == 2
        assert safe_len("hello") == 5

    def test_safe_len_returns_zero_for_non_sized_types(self):
        assert safe_len(42) == 0
        assert safe_len(None) == 0
        assert safe_len(True) == 0


class TestTreeTraversal:
    def test_traverse_dict_calls_callback_for_each_key(self):
        data = {"a": 1, "b": 2, "c": 3}
        visited = []

        def callback(key, value, depth):
            visited.append((key, value, depth))

        tree_traversal.traverse_dict(data, callback)
        assert len(visited) == 3
        assert ("a", 1, 0) in visited
        assert ("b", 2, 0) in visited
        assert ("c", 3, 0) in visited

    def test_traverse_dict_traverses_nested_dicts(self):
        data = {"outer": {"inner": "value"}}
        visited = []

        def callback(key, value, depth):
            visited.append((key, depth))

        tree_traversal.traverse_dict(data, callback)
        assert ("outer", 0) in visited
        assert ("inner", 1) in visited

    def test_traverse_dict_handles_non_dict_input(self):
        visited = []

        def callback(key, value, depth):
            visited.append(key)

        tree_traversal.traverse_dict("not a dict", callback)
        tree_traversal.traverse_dict(None, callback)
        assert visited == []

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

        tree_traversal.traverse_schema_node(schema, callback)
        assert 0 in visited_depths
        assert 1 in visited_depths

    def test_traverse_schema_node_traverses_items(self):
        schema = {
            "type": "array",
            "items": {"type": "string"},
        }
        visited = []

        def callback(node, depth):
            visited.append((node.get("type"), depth))

            return None

        tree_traversal.traverse_schema_node(schema, callback)
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

        tree_traversal.traverse_schema_node(schema, callback)
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

            return False

        tree_traversal.traverse_schema_node(schema, callback)
        assert len(visited) == 1
        assert visited[0] == 0

    def test_traverse_schema_node_handles_non_dict_input(self):
        visited = []

        def callback(node, depth):
            visited.append(node)

            return None

        tree_traversal.traverse_schema_node("not a dict", callback)
        tree_traversal.traverse_schema_node(None, callback)
        assert visited == []

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
        paths = tree_analysis.collect_paths(data)
        assert "user" in paths
        assert "user.name" in paths
        assert "user.address" in paths
        assert "user.address.city" in paths
        assert "active" in paths

    def test_collect_paths_with_prefix(self):
        data = {"key": "value"}
        paths = tree_analysis.collect_paths(data, prefix="root")
        assert "root.key" in paths

    def test_collect_paths_returns_empty_for_non_dict(self):
        assert tree_analysis.collect_paths("not a dict") == []
        assert tree_analysis.collect_paths(None) == []

    def test_count_nodes_counts_all_nodes_in_tree(self):
        tree = {
            "a": None,
            "b": {
                "c": None,
                "d": None,
            },
        }
        count = tree_analysis.count_nodes(tree)
        assert count == 4

    def test_count_nodes_returns_zero_for_none(self):
        assert tree_analysis.count_nodes(None) == 0

    def test_count_nodes_returns_zero_for_empty_dict(self):
        assert tree_analysis.count_nodes({}) == 0

    def test_flatten_tree_returns_sorted_list_of_full_paths(self):
        tree = {
            "z": None,
            "a": {
                "b": None,
            },
        }
        paths = tree_analysis.flatten(tree)
        assert paths == ["a", "a.b", "z"]

    def test_flatten_tree_returns_empty_for_none(self):
        assert tree_analysis.flatten(None) == []

    def test_flatten_tree_with_prefix(self):
        tree = {"key": None}
        paths = tree_analysis.flatten(tree, prefix="root")
        assert "root.key" in paths

    def test_tree_contains_returns_true_when_larger_contains_smaller(self):
        larger = {"a": {"b": None, "c": None}, "d": None}
        smaller = {"a": {"b": None}}
        assert tree_operations.contains(larger, smaller) is True

    def test_tree_contains_returns_false_when_key_missing(self):
        larger = {"a": None}
        smaller = {"b": None}
        assert tree_operations.contains(larger, smaller) is False

    def test_tree_contains_returns_false_when_nested_key_missing(self):
        larger = {"a": {"b": None}}
        smaller = {"a": {"c": None}}
        assert tree_operations.contains(larger, smaller) is False

    def test_tree_contains_with_none_smaller_returns_true(self):
        larger = {"a": None}
        assert tree_operations.contains(larger, None) is True

    def test_tree_contains_with_none_larger_and_non_none_smaller_returns_false(self):
        smaller = {"a": None}
        assert tree_operations.contains(None, smaller) is False

    def test_tree_contains_with_both_none_returns_true(self):
        assert tree_operations.contains(None, None) is True

    def test_merge_trees_combines_two_trees(self):
        tree1 = {"a": None, "b": None}
        tree2 = {"c": None, "d": None}
        merged = tree_operations.merge(tree1, tree2)
        assert "a" in merged
        assert "b" in merged
        assert "c" in merged
        assert "d" in merged

    def test_merge_trees_handles_none_tree1(self):
        tree2 = {"a": None}
        merged = tree_operations.merge(None, tree2)
        assert merged == tree2

    def test_merge_trees_handles_none_tree2(self):
        tree1 = {"a": None}
        merged = tree_operations.merge(tree1, None)
        assert merged == tree1

    def test_merge_trees_handles_both_none(self):
        merged = tree_operations.merge(None, None)
        assert merged is None

    def test_merge_trees_recursively_merges_nested_dicts(self):
        tree1 = {"a": {"b": None}}
        tree2 = {"a": {"c": None}}
        merged = tree_operations.merge(tree1, tree2)
        assert merged == {"a": {"b": None, "c": None}}

    def test_merge_trees_overwrites_none_with_subtree(self):
        tree1 = {"a": None}
        tree2 = {"a": {"b": None}}
        merged = tree_operations.merge(tree1, tree2)
        assert merged == {"a": {"b": None}}

    def test_merge_trees_preserves_subtree_when_other_is_none(self):
        tree1 = {"a": {"b": None}}
        tree2 = {"a": None}
        merged = tree_operations.merge(tree1, tree2)
        assert merged == {"a": {"b": None}}

    def test_merge_trees_does_not_modify_original_trees(self):
        tree1 = {"a": None}
        tree2 = {"b": None}
        tree1_copy = dict(tree1)
        tree2_copy = dict(tree2)
        tree_operations.merge(tree1, tree2)
        assert tree1 == tree1_copy
        assert tree2 == tree2_copy
