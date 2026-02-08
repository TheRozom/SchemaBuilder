import pytest

from src.bl.analyzer.groupers import Grouper
from src.bl.analyzer.trees import TreeBuilder
from src.shared.models import JsonStructure


class TestGrouper:
    @pytest.fixture
    def grouper(self) -> Grouper:
        return Grouper()

    @pytest.fixture
    def tree_builder(self) -> TreeBuilder:
        return TreeBuilder()

    def _build_structures(self, tree_builder, data_list):
        structures = []
        for idx, item in enumerate(data_list):
            tree = tree_builder.build(item)
            structures.append(
                JsonStructure(
                    index=idx,
                    tree=tree,
                    key_count=tree_builder.count_nodes(tree),
                )
            )
        return structures

    def test_user_records_with_different_optional_fields_are_grouped(
        self, grouper: Grouper, tree_builder: TreeBuilder
    ):
        data = [
            {
                "id": 1,
                "name": "Alice",
                "email": "alice@test.com",
                "referralCode": "REF123",
            },
            {
                "id": 2,
                "name": "Bob",
                "email": "bob@test.com",
                "profile": {"age": 30},
            },
        ]
        structures = self._build_structures(tree_builder, data)
        groups = grouper.group_by_similarity(structures)
        assert len(groups) == 1
        assert sorted(groups[0].indices) == [0, 1]

    def test_high_similarity_structures_are_grouped(
        self, grouper: Grouper, tree_builder: TreeBuilder
    ):
        data = [
            {"name": "Alice", "age": 30, "email": "alice@test.com"},
            {"name": "Bob", "age": 25, "phone": "555-1234"},
        ]
        structures = self._build_structures(tree_builder, data)
        groups = grouper.group_by_similarity(structures)
        assert len(groups) == 1

    def test_low_similarity_structures_are_separate(
        self, grouper: Grouper, tree_builder: TreeBuilder
    ):
        data = [
            {"user": {"name": "Alice"}},
            {"product": {"sku": "ABC", "price": 99.99}},
        ]
        structures = self._build_structures(tree_builder, data)
        groups = grouper.group_by_similarity(structures)
        assert len(groups) == 2

    def test_containment_still_works_as_fast_path(
        self, grouper: Grouper, tree_builder: TreeBuilder
    ):
        data = [
            {"name": "Alice"},
            {"name": "Bob", "age": 30},
            {"name": "Charlie", "age": 25, "email": "charlie@test.com"},
        ]
        structures = self._build_structures(tree_builder, data)
        groups = grouper.group_by_similarity(structures)
        assert len(groups) == 1
        assert sorted(groups[0].indices) == [0, 1, 2]

    def test_identical_structures_grouped(self, grouper: Grouper, tree_builder: TreeBuilder):
        data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
        ]
        structures = self._build_structures(tree_builder, data)
        groups = grouper.group_by_similarity(structures)
        assert len(groups) == 1

    def test_completely_different_structures_not_grouped(
        self, grouper: Grouper, tree_builder: TreeBuilder
    ):
        data = [
            {"user": {"name": "Alice"}},
            {"product": {"id": 123}},
            {"config": {"version": "1.0"}},
        ]
        structures = self._build_structures(tree_builder, data)
        groups = grouper.group_by_similarity(structures)
        assert len(groups) == 3

    def test_single_structure_returns_one_group(
        self, grouper: Grouper, tree_builder: TreeBuilder
    ):
        data = [{"name": "Alice", "age": 30}]
        structures = self._build_structures(tree_builder, data)
        groups = grouper.group_by_similarity(structures)
        assert len(groups) == 1
        assert groups[0].indices == [0]

    def test_nested_contacts_with_optional_fields_are_grouped(
        self, grouper: Grouper, tree_builder: TreeBuilder
    ):
        data = [
            {
                "id": 1,
                "name": "Alice",
                "contacts": {"email": "alice@test.com", "phone": "555-1234"},
            },
            {
                "id": 2,
                "name": "Bob",
                "contacts": {"email": "bob@test.com"},
                "referralCode": "REF123",
            },
        ]
        structures = self._build_structures(tree_builder, data)
        groups = grouper.group_by_similarity(structures)
        assert len(groups) == 1
        assert sorted(groups[0].indices) == [0, 1]

    def test_empty_list_returns_no_groups(self, grouper: Grouper):
        groups = grouper.group_by_similarity([])
        assert groups == []
