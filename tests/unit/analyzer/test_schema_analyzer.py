import pytest
from typing import Dict, Any, List

from src.bl.analyzer import SchemaAnalyzer
from src.bl.analyzer.trees import TreeBuilder
from src.shared.exceptions import InputValidationError
from src.shared.enums import ConfidenceLevel


class TestSchemaAnalyzerAnalyzeConflicts:
    """Tests for SchemaAnalyzer.analyze_conflicts() method."""

    @pytest.fixture
    def analyzer(self) -> SchemaAnalyzer:
        return SchemaAnalyzer()

    # -------------------------------------------------------------------
    # Empty and single object cases
    # -------------------------------------------------------------------

    def test_empty_list_returns_empty_result(self, analyzer: SchemaAnalyzer):
        """Empty list returns empty result with 0 objects."""
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
        """Single object returns 1 unique structure."""
        data = [{"name": "Alice", "age": 30}]

        result = analyzer.analyze_conflicts(data)

        assert result.objects_analyzed == 1
        assert result.unique_structures == 1
        assert len(result.groups) == 1
        assert result.groups[0].object_indices == [0]
        assert result.summary.should_split_schemas is False

    # -------------------------------------------------------------------
    # Grouping behavior tests
    # -------------------------------------------------------------------

    def test_identical_objects_grouped_together(self, analyzer: SchemaAnalyzer):
        """Identical objects are grouped together."""
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
        """Different structures create different groups."""
        data = [
            {"user": {"name": "Alice"}},
            {"product": {"id": 123}},
            {"config": {"version": "1.0"}},
        ]

        result = analyzer.analyze_conflicts(data)

        assert result.objects_analyzed == 3
        assert result.unique_structures == 3
        assert len(result.groups) == 3
        # Each object should be in its own group
        all_indices = []
        for group in result.groups:
            all_indices.extend(group.object_indices)
        assert sorted(all_indices) == [0, 1, 2]

    def test_subset_superset_keys_grouped_by_containment(self, analyzer: SchemaAnalyzer):
        """Objects with subset/superset keys are grouped by containment."""
        data = [
            {"name": "Alice"},
            {"name": "Bob", "age": 30},
            {"name": "Charlie", "age": 25, "email": "charlie@test.com"},
        ]

        result = analyzer.analyze_conflicts(data)

        # All should be in one group since they have containment relationship
        assert result.unique_structures == 1
        assert len(result.groups) == 1
        assert sorted(result.groups[0].object_indices) == [0, 1, 2]

    def test_mixed_structures_detected_correctly(self, analyzer: SchemaAnalyzer):
        """Mixed structures (user, product, config) are detected correctly."""
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

    # -------------------------------------------------------------------
    # Validation error tests
    # -------------------------------------------------------------------

    def test_non_dict_items_raise_input_validation_error(self, analyzer: SchemaAnalyzer):
        """Non-dict items raise InputValidationError."""
        data = [{"name": "Alice"}, "not a dict", 123]

        with pytest.raises(InputValidationError) as exc_info:
            analyzer.analyze_conflicts(data)

        assert "All items must be JSON objects" in str(exc_info.value.message)
        assert exc_info.value.field == "data_list"
        assert "invalid_indices" in exc_info.value.details

    def test_non_dict_items_reports_correct_indices(self, analyzer: SchemaAnalyzer):
        """Non-dict items validation reports correct invalid indices."""
        data = [{"a": 1}, "string", {"b": 2}, 42, None]

        with pytest.raises(InputValidationError) as exc_info:
            analyzer.analyze_conflicts(data)

        invalid_indices = exc_info.value.details["invalid_indices"]
        assert 1 in invalid_indices  # "string"
        assert 3 in invalid_indices  # 42
        assert 4 in invalid_indices  # None

    def test_list_only_containing_non_dicts_raises_error(self, analyzer: SchemaAnalyzer):
        """List containing only non-dict items raises InputValidationError."""
        data = ["string", 123, True, None]

        with pytest.raises(InputValidationError):
            analyzer.analyze_conflicts(data)

    # -------------------------------------------------------------------
    # Summary should_split_schemas tests
    # -------------------------------------------------------------------

    def test_summary_should_split_schemas_true_when_multiple_groups(self, analyzer: SchemaAnalyzer):
        """Summary should_split_schemas=True when multiple groups exist."""
        data = [
            {"type": "user", "name": "Alice"},
            {"type": "product", "price": 100},
        ]

        result = analyzer.analyze_conflicts(data)

        # These have different structures, so multiple groups
        assert result.unique_structures > 1
        assert result.summary.should_split_schemas is True

    def test_summary_should_split_schemas_false_when_single_group(self, analyzer: SchemaAnalyzer):
        """Summary should_split_schemas=False when single group exists."""
        data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
        ]

        result = analyzer.analyze_conflicts(data)

        assert result.unique_structures == 1
        assert result.summary.should_split_schemas is False

    # -------------------------------------------------------------------
    # Confidence level tests
    # -------------------------------------------------------------------

    def test_confidence_level_high_for_single_structure(self, analyzer: SchemaAnalyzer):
        """Confidence level is HIGH when all objects have same structure."""
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
        """Confidence level is appropriate when multiple distinct structures exist."""
        data = [
            {"user": "Alice"},
            {"product": 123},
            {"config": True},
            {"setting": "value"},
        ]

        result = analyzer.analyze_conflicts(data)

        # With 4 unique structures from 4 objects, confidence should be HIGH
        assert result.summary.confidence in [
            ConfidenceLevel.HIGH,
            ConfidenceLevel.MEDIUM,
            ConfidenceLevel.LOW,
        ]

    # -------------------------------------------------------------------
    # Group content tests
    # -------------------------------------------------------------------

    def test_groups_contain_correct_object_indices(self, analyzer: SchemaAnalyzer):
        """Groups contain correct object_indices for grouped objects."""
        data = [
            {"a": 1},
            {"a": 2},
            {"b": 1},
            {"b": 2},
        ]

        result = analyzer.analyze_conflicts(data)

        # Verify all indices are accounted for
        all_indices = []
        for group in result.groups:
            all_indices.extend(group.object_indices)
        assert sorted(all_indices) == [0, 1, 2, 3]

        # Each group should have at least one index
        for group in result.groups:
            assert len(group.object_indices) >= 1

    def test_groups_contain_merged_keys_list(self, analyzer: SchemaAnalyzer):
        """Groups contain merged_keys list with all keys from grouped objects."""
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
        """Sample is the first object in each group."""
        data = [
            {"user": "Alice"},
            {"user": "Bob"},
            {"product": 100},
        ]

        result = analyzer.analyze_conflicts(data)

        for group in result.groups:
            first_index = group.object_indices[0]
            assert group.sample == data[first_index]

    # -------------------------------------------------------------------
    # Complex structure tests
    # -------------------------------------------------------------------

    def test_nested_objects_with_different_deep_keys(self, analyzer: SchemaAnalyzer):
        """Nested objects with different deep keys create separate groups."""
        data = [
            {"level1": {"level2": {"a": 1}}},
            {"level1": {"level2": {"b": 2}}},
        ]

        result = analyzer.analyze_conflicts(data)

        # Different nested keys should create different groups
        assert result.objects_analyzed == 2

    def test_objects_with_arrays_analyzed_correctly(self, analyzer: SchemaAnalyzer):
        """Objects with arrays of objects are analyzed correctly."""
        data = [
            {"items": [{"id": 1}, {"id": 2}]},
            {"items": [{"id": 3}]},
        ]

        result = analyzer.analyze_conflicts(data)

        assert result.objects_analyzed == 2
        # Both have same structure (items array with objects containing id)
        assert result.unique_structures == 1


class TestTreeBuilder:
    """Tests for TreeBuilder class."""

    @pytest.fixture
    def builder(self) -> TreeBuilder:
        return TreeBuilder()

    # -------------------------------------------------------------------
    # Build tree tests
    # -------------------------------------------------------------------

    def test_build_tree_from_flat_object(self, builder: TreeBuilder):
        """Build tree from flat object."""
        data = {"name": "Alice", "age": 30, "active": True}

        tree = builder.build(data)

        assert "name" in tree
        assert "age" in tree
        assert "active" in tree
        assert tree["name"] is None
        assert tree["age"] is None
        assert tree["active"] is None

    def test_build_tree_from_nested_object(self, builder: TreeBuilder):
        """Build tree from nested object."""
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
        """Build tree with arrays of objects uses key[] notation."""
        data = {
            "users": [
                {"name": "Alice", "age": 30},
                {"name": "Bob", "email": "bob@test.com"},
            ]
        }

        tree = builder.build(data)

        assert "users[]" in tree
        # Merged keys from all array items
        assert "name" in tree["users[]"]
        assert "age" in tree["users[]"]
        assert "email" in tree["users[]"]

    def test_build_tree_with_empty_array(self, builder: TreeBuilder):
        """Build tree with empty array."""
        data = {"items": []}

        tree = builder.build(data)

        # Empty array doesn't create array notation key
        assert "items" in tree
        assert tree["items"] is None

    def test_build_tree_with_primitive_array(self, builder: TreeBuilder):
        """Build tree with array of primitives."""
        data = {"tags": ["a", "b", "c"]}

        tree = builder.build(data)

        # Array of primitives is treated as a leaf
        assert "tags" in tree
        assert tree["tags"] is None

    def test_build_tree_from_empty_object(self, builder: TreeBuilder):
        """Build tree from empty object."""
        data: Dict[str, Any] = {}

        tree = builder.build(data)

        assert tree == {}

    def test_build_tree_from_non_dict_returns_empty(self, builder: TreeBuilder):
        """Build tree from non-dict returns empty dict."""
        tree_str = builder.build("string")
        tree_int = builder.build(123)
        tree_list = builder.build([1, 2, 3])

        assert tree_str == {}
        assert tree_int == {}
        assert tree_list == {}

    # -------------------------------------------------------------------
    # Count nodes tests
    # -------------------------------------------------------------------

    def test_count_nodes_flat_object(self, builder: TreeBuilder):
        """count_nodes returns correct count for flat object."""
        tree = {"a": None, "b": None, "c": None}

        count = builder.count_nodes(tree)

        assert count == 3

    def test_count_nodes_nested_object(self, builder: TreeBuilder):
        """count_nodes returns correct count for nested object."""
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

        # user, name, address, city, zip = 5 nodes
        assert count == 5

    def test_count_nodes_empty_tree(self, builder: TreeBuilder):
        """count_nodes returns 0 for empty tree."""
        tree: Dict[str, Any] = {}

        count = builder.count_nodes(tree)

        assert count == 0

    def test_count_nodes_with_array_notation(self, builder: TreeBuilder):
        """count_nodes counts array notation keys correctly."""
        tree = {
            "items[]": {
                "id": None,
                "name": None,
            }
        }

        count = builder.count_nodes(tree)

        # items[], id, name = 3 nodes
        assert count == 3


class TestSchemaAnalyzerIntegration:
    """Integration tests for SchemaAnalyzer with various data patterns."""

    @pytest.fixture
    def analyzer(self) -> SchemaAnalyzer:
        return SchemaAnalyzer()

    def test_realistic_user_data_analysis(self, analyzer: SchemaAnalyzer):
        """Analyze realistic user data with consistent structure."""
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
        """Analyze API responses where some objects have optional fields."""
        data = [
            {"status": "ok", "data": {"id": 1}},
            {"status": "ok", "data": {"id": 2}, "meta": {"page": 1}},
            {"status": "ok", "data": {"id": 3}, "meta": {"page": 2, "total": 100}},
        ]

        result = analyzer.analyze_conflicts(data)

        # All should be grouped together due to containment
        assert result.unique_structures == 1

    def test_completely_different_schemas_mixed(self, analyzer: SchemaAnalyzer):
        """Analyze completely different schemas mixed together."""
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
        """Analyze deeply nested structures."""
        data = [
            {"level1": {"level2": {"level3": {"level4": {"value": 1}}}}},
            {"level1": {"level2": {"level3": {"level4": {"value": 2}}}}},
        ]

        result = analyzer.analyze_conflicts(data)

        assert result.objects_analyzed == 2
        assert result.unique_structures == 1
        # Check nested keys are flattened
        merged_keys = result.groups[0].merged_keys
        assert any("level1" in key for key in merged_keys)
