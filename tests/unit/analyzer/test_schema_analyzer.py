from typing import Any

import pytest

from src.bl.analyzer import SchemaAnalyzer
from src.bl.analyzer.trees import TreeBuilder
from src.shared.enums import ConfidenceLevel
from src.shared.exceptions import InputValidationError


class TestSchemaAnalyzerAnalyzeConflicts:
    @pytest.fixture
    def analyzer(self) -> SchemaAnalyzer:
        return SchemaAnalyzer()

    def test_empty_list_returns_empty_result(self, analyzer: SchemaAnalyzer):
        result = analyzer.analyze_conflicts([])
        assert result.objects_analyzed == 0
        assert result.unique_structures == 0
        assert result.groups == []
        assert result.similarity_matrix == []
        assert result.summary.total_objects == 0
        assert result.summary.unique_structures == 0
        assert result.summary.should_split_schemas is False
        assert result.summary.confidence == ConfidenceLevel.HIGH

    def test_single_object_returns_one_unique_structure(self, analyzer: SchemaAnalyzer):
        data = [{"name": "Alice", "age": 30}]
        result = analyzer.analyze_conflicts(data)
        assert result.objects_analyzed == 1
        assert result.unique_structures == 1
        assert len(result.groups) == 1
        assert result.groups[0].object_indices == [0]
        assert result.summary.should_split_schemas is False

    def test_identical_objects_grouped_together(self, analyzer: SchemaAnalyzer):
        data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
            {"name": "Charlie", "age": 35},
        ]
        result = analyzer.analyze_conflicts(data)
        assert result.objects_analyzed == 3
        assert result.unique_structures == 1
        assert len(result.groups) == 1
        assert sorted(result.groups[0].object_indices) == [0, 1, 2]

    def test_different_structures_create_different_groups(self, analyzer: SchemaAnalyzer):
        data = [
            {"user": {"name": "Alice"}},
            {"product": {"id": 123}},
            {"config": {"version": "1.0"}},
        ]
        result = analyzer.analyze_conflicts(data)
        assert result.objects_analyzed == 3
        assert result.unique_structures == 3
        assert len(result.groups) == 3
        all_indices = []

        for group in result.groups:
            all_indices.extend(group.object_indices)

        assert sorted(all_indices) == [0, 1, 2]

    def test_subset_superset_keys_grouped_by_containment(self, analyzer: SchemaAnalyzer):
        data = [
            {"name": "Alice"},
            {"name": "Bob", "age": 30},
            {"name": "Charlie", "age": 25, "email": "charlie@test.com"},
        ]
        result = analyzer.analyze_conflicts(data)
        assert result.unique_structures == 1
        assert len(result.groups) == 1
        assert sorted(result.groups[0].object_indices) == [0, 1, 2]

    def test_mixed_structures_detected_correctly(self, analyzer: SchemaAnalyzer):
        data = [
            {"user": {"name": "John", "email": "john@test.com"}},
            {"user": {"name": "Jane", "email": "jane@test.com"}},
            {"product": {"id": 123, "price": 99.99}},
            {"product": {"id": 456, "price": 49.99}},
            {"config": {"version": "1.0", "debug": True}},
        ]
        result = analyzer.analyze_conflicts(data)
        assert result.objects_analyzed == 5
        assert result.unique_structures == 3
        assert len(result.groups) == 3
        assert result.summary.should_split_schemas is True

    def test_non_dict_items_raise_input_validation_error(self, analyzer: SchemaAnalyzer):
        data = [{"name": "Alice"}, "not a dict", 123]

        with pytest.raises(InputValidationError) as exc_info:
            analyzer.analyze_conflicts(data)

        assert "All items must be JSON objects" in str(exc_info.value.message)
        assert exc_info.value.field == "data_list"
        assert "invalid_indices" in exc_info.value.details

    def test_non_dict_items_reports_correct_indices(self, analyzer: SchemaAnalyzer):
        data = [{"a": 1}, "string", {"b": 2}, 42, None]

        with pytest.raises(InputValidationError) as exc_info:
            analyzer.analyze_conflicts(data)

        invalid_indices = exc_info.value.details["invalid_indices"]
        assert 1 in invalid_indices
        assert 3 in invalid_indices
        assert 4 in invalid_indices

    def test_list_only_containing_non_dicts_raises_error(self, analyzer: SchemaAnalyzer):
        data = ["string", 123, True, None]

        with pytest.raises(InputValidationError):
            analyzer.analyze_conflicts(data)

    def test_summary_should_split_schemas_true_when_multiple_groups(self, analyzer: SchemaAnalyzer):
        data = [
            {"type": "user", "name": "Alice"},
            {"type": "product", "price": 100},
        ]
        result = analyzer.analyze_conflicts(data)
        assert result.unique_structures > 1
        assert result.summary.should_split_schemas is True

    def test_summary_should_split_schemas_false_when_single_group(self, analyzer: SchemaAnalyzer):
        data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
        ]
        result = analyzer.analyze_conflicts(data)
        assert result.unique_structures == 1
        assert result.summary.should_split_schemas is False

    def test_confidence_level_high_for_single_structure(self, analyzer: SchemaAnalyzer):
        data = [
            {"id": 1, "name": "A"},
            {"id": 2, "name": "B"},
            {"id": 3, "name": "C"},
        ]
        result = analyzer.analyze_conflicts(data)
        assert result.summary.confidence == ConfidenceLevel.HIGH

    def test_confidence_level_appropriate_for_multiple_distinct_structures(
        self, analyzer: SchemaAnalyzer
    ):
        data = [
            {"user": "Alice"},
            {"product": 123},
            {"config": True},
            {"setting": "value"},
        ]
        result = analyzer.analyze_conflicts(data)
        assert result.summary.confidence in [
            ConfidenceLevel.HIGH,
            ConfidenceLevel.MEDIUM,
            ConfidenceLevel.LOW,
        ]

    def test_groups_contain_correct_object_indices(self, analyzer: SchemaAnalyzer):
        data = [
            {"a": 1},
            {"a": 2},
            {"b": 1},
            {"b": 2},
        ]
        result = analyzer.analyze_conflicts(data)
        all_indices = []

        for group in result.groups:
            all_indices.extend(group.object_indices)

        assert sorted(all_indices) == [0, 1, 2, 3]

        for group in result.groups:
            assert len(group.object_indices) >= 1

    def test_groups_contain_merged_keys_list(self, analyzer: SchemaAnalyzer):
        data = [
            {"name": "Alice"},
            {"name": "Bob", "age": 30},
        ]
        result = analyzer.analyze_conflicts(data)
        assert len(result.groups) == 1
        merged_keys = result.groups[0].merged_keys
        assert "name" in merged_keys
        assert "age" in merged_keys

    def test_sample_is_first_object_in_each_group(self, analyzer: SchemaAnalyzer):
        data = [
            {"user": "Alice"},
            {"user": "Bob"},
            {"product": 100},
        ]
        result = analyzer.analyze_conflicts(data)

        for group in result.groups:
            first_index = group.object_indices[0]
            assert group.sample == data[first_index]

    def test_nested_objects_with_different_deep_keys(self, analyzer: SchemaAnalyzer):
        data = [
            {"level1": {"level2": {"a": 1}}},
            {"level1": {"level2": {"b": 2}}},
        ]
        result = analyzer.analyze_conflicts(data)
        assert result.objects_analyzed == 2

    def test_objects_with_arrays_analyzed_correctly(self, analyzer: SchemaAnalyzer):
        data = [
            {"items": [{"id": 1}, {"id": 2}]},
            {"items": [{"id": 3}]},
        ]
        result = analyzer.analyze_conflicts(data)
        assert result.objects_analyzed == 2
        assert result.unique_structures == 1


class TestTreeBuilder:
    @pytest.fixture
    def builder(self) -> TreeBuilder:
        return TreeBuilder()

    def test_build_tree_from_flat_object(self, builder: TreeBuilder):
        data = {"name": "Alice", "age": 30, "active": True}
        tree = builder.build(data)
        assert "name" in tree
        assert "age" in tree
        assert "active" in tree
        assert tree["name"] is None
        assert tree["age"] is None
        assert tree["active"] is None

    def test_build_tree_from_nested_object(self, builder: TreeBuilder):
        data = {
            "user": {
                "name": "Alice",
                "address": {
                    "city": "NYC",
                    "zip": "10001",
                },
            }
        }
        tree = builder.build(data)
        assert "user" in tree
        assert isinstance(tree["user"], dict)
        assert "name" in tree["user"]
        assert "address" in tree["user"]
        assert isinstance(tree["user"]["address"], dict)
        assert "city" in tree["user"]["address"]
        assert "zip" in tree["user"]["address"]

    def test_build_tree_with_arrays_of_objects(self, builder: TreeBuilder):
        data = {
            "users": [
                {"name": "Alice", "age": 30},
                {"name": "Bob", "email": "bob@test.com"},
            ]
        }
        tree = builder.build(data)
        assert "users[]" in tree
        assert "name" in tree["users[]"]
        assert "age" in tree["users[]"]
        assert "email" in tree["users[]"]

    def test_build_tree_with_empty_array(self, builder: TreeBuilder):
        data = {"items": []}
        tree = builder.build(data)
        assert "items" in tree
        assert tree["items"] is None

    def test_build_tree_with_primitive_array(self, builder: TreeBuilder):
        data = {"tags": ["a", "b", "c"]}
        tree = builder.build(data)
        assert "tags" in tree
        assert tree["tags"] is None

    def test_build_tree_from_empty_object(self, builder: TreeBuilder):
        data: dict[str, Any] = {}
        tree = builder.build(data)
        assert tree == {}

    def test_build_tree_from_non_dict_returns_empty(self, builder: TreeBuilder):
        tree_str = builder.build("string")
        tree_int = builder.build(123)
        tree_list = builder.build([1, 2, 3])
        assert tree_str == {}
        assert tree_int == {}
        assert tree_list == {}

    def test_count_nodes_flat_object(self, builder: TreeBuilder):
        tree = {"a": None, "b": None, "c": None}
        count = builder.count_nodes(tree)
        assert count == 3

    def test_count_nodes_nested_object(self, builder: TreeBuilder):
        tree = {
            "user": {
                "name": None,
                "address": {
                    "city": None,
                    "zip": None,
                },
            }
        }
        count = builder.count_nodes(tree)
        assert count == 5

    def test_count_nodes_empty_tree(self, builder: TreeBuilder):
        tree: dict[str, Any] = {}
        count = builder.count_nodes(tree)
        assert count == 0

    def test_count_nodes_with_array_notation(self, builder: TreeBuilder):
        tree = {
            "items[]": {
                "id": None,
                "name": None,
            }
        }
        count = builder.count_nodes(tree)
        assert count == 3


class TestSchemaAnalyzerIntegration:
    @pytest.fixture
    def analyzer(self) -> SchemaAnalyzer:
        return SchemaAnalyzer()

    def test_realistic_user_data_analysis(self, analyzer: SchemaAnalyzer):
        data = [
            {"id": 1, "name": "Alice", "email": "alice@test.com", "active": True},
            {"id": 2, "name": "Bob", "email": "bob@test.com", "active": False},
            {"id": 3, "name": "Charlie", "email": "charlie@test.com", "active": True},
        ]
        result = analyzer.analyze_conflicts(data)
        assert result.objects_analyzed == 3
        assert result.unique_structures == 1
        assert result.summary.should_split_schemas is False
        assert "id" in result.groups[0].merged_keys
        assert "name" in result.groups[0].merged_keys
        assert "email" in result.groups[0].merged_keys
        assert "active" in result.groups[0].merged_keys

    def test_api_response_with_optional_fields(self, analyzer: SchemaAnalyzer):
        data = [
            {"status": "ok", "data": {"id": 1}},
            {"status": "ok", "data": {"id": 2}, "meta": {"page": 1}},
            {"status": "ok", "data": {"id": 3}, "meta": {"page": 2, "total": 100}},
        ]
        result = analyzer.analyze_conflicts(data)
        assert result.unique_structures == 1

    def test_completely_different_schemas_mixed(self, analyzer: SchemaAnalyzer):
        data = [
            {"user": {"id": 1, "name": "Alice"}},
            {"product": {"sku": "ABC", "price": 99.99}},
            {"order": {"orderId": "ORD-1", "items": [{"qty": 2}]}},
            {"config": {"version": "1.0", "features": {"dark_mode": True}}},
        ]
        result = analyzer.analyze_conflicts(data)
        assert result.objects_analyzed == 4
        assert result.unique_structures == 4
        assert result.summary.should_split_schemas is True
        assert len(result.groups) == 4

    def test_deeply_nested_structures(self, analyzer: SchemaAnalyzer):
        data = [
            {"level1": {"level2": {"level3": {"level4": {"value": 1}}}}},
            {"level1": {"level2": {"level3": {"level4": {"value": 2}}}}},
        ]
        result = analyzer.analyze_conflicts(data)
        assert result.objects_analyzed == 2
        assert result.unique_structures == 1
        merged_keys = result.groups[0].merged_keys
        assert any("level1" in key for key in merged_keys)
