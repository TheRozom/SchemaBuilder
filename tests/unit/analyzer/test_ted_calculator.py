import pytest

from src.bl.analyzer.trees import TedCalculator


class TestTedCalculator:
    @pytest.fixture
    def calculator(self) -> TedCalculator:
        return TedCalculator()

    def test_identical_trees_return_100_similarity(self, calculator: TedCalculator):
        tree = {"name": None, "age": None, "email": None}
        result = calculator.calculate_similarity(tree, tree)
        assert result == 100.0

    def test_empty_trees_return_100_similarity(self, calculator: TedCalculator):
        result = calculator.calculate_similarity({}, {})
        assert result == 100.0

    def test_completely_disjoint_trees_return_low_similarity(self, calculator: TedCalculator):
        tree_a = {"name": None, "age": None, "email": None}
        tree_b = {"product": None, "price": None, "sku": None}
        result = calculator.calculate_similarity(tree_a, tree_b)
        assert result < 50

    def test_single_leaf_difference_returns_high_similarity(self, calculator: TedCalculator):
        tree_a = {"name": None, "age": None, "email": None}
        tree_b = {"name": None, "age": None, "phone": None}
        result = calculator.calculate_similarity(tree_a, tree_b)
        assert result > 60

    def test_nested_tree_similarity(self, calculator: TedCalculator):
        tree_a = {"user": {"name": None, "age": None}}
        tree_b = {"user": {"name": None, "email": None}}
        result = calculator.calculate_similarity(tree_a, tree_b)
        assert result > 50

    def test_subset_trees_return_high_similarity(self, calculator: TedCalculator):
        tree_a = {"name": None, "age": None}
        tree_b = {"name": None, "age": None, "email": None}
        result = calculator.calculate_similarity(tree_a, tree_b)
        assert result > 60

    def test_one_empty_one_populated_returns_low_similarity(self, calculator: TedCalculator):
        tree_a = {}
        tree_b = {"name": None, "age": None, "email": None}
        result = calculator.calculate_similarity(tree_a, tree_b)
        assert result < 50

    def test_deeply_nested_identical_trees(self, calculator: TedCalculator):
        tree = {"level1": {"level2": {"level3": {"value": None}}}}
        result = calculator.calculate_similarity(tree, tree)
        assert result == 100.0

    def test_dict_tree_to_zss_node_creates_correct_structure(self, calculator: TedCalculator):
        tree = {"name": None, "address": {"city": None}}
        node = calculator._dict_tree_to_zss_node(tree, "root")
        from zss import Node

        children = Node.get_children(node)
        child_labels = [Node.get_label(c) for c in children]
        assert "name" in child_labels
        assert "address" in child_labels

    def test_symmetry(self, calculator: TedCalculator):
        tree_a = {"name": None, "age": None}
        tree_b = {"name": None, "email": None, "phone": None}
        result_ab = calculator.calculate_similarity(tree_a, tree_b)
        result_ba = calculator.calculate_similarity(tree_b, tree_a)
        assert result_ab == result_ba
