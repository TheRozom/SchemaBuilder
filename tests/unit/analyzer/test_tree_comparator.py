import pytest

from src.bl.analyzer.trees import TreeBuilder, TreeComparator


class TestKeySimlarity:
    @pytest.fixture
    def comparator(self) -> TreeComparator:
        return TreeComparator()

    @pytest.fixture
    def tree_builder(self) -> TreeBuilder:
        return TreeBuilder()

    def test_identical_trees_return_100(self, comparator, tree_builder):
        tree = tree_builder.build({"name": "Alice", "age": 30})
        assert comparator.key_similarity(tree, tree) == 100.0

    def test_both_empty_returns_100(self, comparator):
        assert comparator.key_similarity({}, {}) == 100.0

    def test_one_empty_returns_0(self, comparator, tree_builder):
        tree = tree_builder.build({"name": "Alice"})
        assert comparator.key_similarity(tree, {}) == 0.0
        assert comparator.key_similarity({}, tree) == 0.0

    def test_completely_disjoint_returns_0(self, comparator, tree_builder):
        tree_a = tree_builder.build({"name": "Alice"})
        tree_b = tree_builder.build({"product": "Widget"})
        assert comparator.key_similarity(tree_a, tree_b) == 0.0

    def test_partial_overlap(self, comparator, tree_builder):
        tree_a = tree_builder.build({"name": "Alice", "age": 30, "email": "a@b.com"})
        tree_b = tree_builder.build({"name": "Bob", "age": 25, "phone": "555"})
        similarity = comparator.key_similarity(tree_a, tree_b)
        assert similarity == pytest.approx(66.67, abs=0.01)

    def test_nested_structures(self, comparator, tree_builder):
        tree_a = tree_builder.build({
            "id": 1,
            "name": "Alice",
            "contacts": {"email": "a@b.com", "phone": "555"},
        })
        tree_b = tree_builder.build({
            "id": 2,
            "name": "Bob",
            "contacts": {"email": "b@b.com"},
            "referralCode": "REF",
        })
        similarity = comparator.key_similarity(tree_a, tree_b)
        assert similarity > 60

    def test_subset_returns_100(self, comparator, tree_builder):
        tree_a = tree_builder.build({"name": "Alice", "age": 30})
        tree_b = tree_builder.build({"name": "Bob", "age": 25, "email": "b@b.com"})
        similarity = comparator.key_similarity(tree_a, tree_b)
        assert similarity == 100.0
