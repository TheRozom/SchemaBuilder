from typing import Any, Dict, List

from src.bl.analyzer.trees import TreeComparator
from src.shared.models import GroupData, JsonStructure


class Grouper:
    def __init__(self) -> None:
        self.comparator = TreeComparator()

    def group_by_containment(self, json_structures: List[JsonStructure]) -> List[GroupData]:
        groups: List[GroupData] = []
        used_indices = set()

        for i, struct_i in enumerate(json_structures):
            if i in used_indices:
                continue

            group = self._create_initial_group(struct_i, i)
            used_indices.add(i)

            group = self._add_compatible_structures(
                group, json_structures, used_indices, start_index=i + 1
            )

            groups.append(group)

        return groups

    def _create_initial_group(self, structure: JsonStructure, index: int) -> GroupData:
        return GroupData(indices=[index], merged_tree=structure.tree)

    def _add_compatible_structures(
        self,
        group: GroupData,
        json_structures: List[JsonStructure],
        used_indices: set,
        start_index: int,
    ) -> GroupData:
        for j, struct_j in enumerate(json_structures[start_index:], start=start_index):
            if j in used_indices:
                continue

            if self._are_structures_compatible(group.merged_tree, struct_j.tree):
                group = self._merge_structure_into_group(group, struct_j, j)
                used_indices.add(j)

        return group

    def _are_structures_compatible(self, tree_a: Dict[str, Any], tree_b: Dict[str, Any]) -> bool:
        return self.comparator.contains(tree_a, tree_b) or self.comparator.contains(tree_b, tree_a)

    def _merge_structure_into_group(
        self, group: GroupData, structure: JsonStructure, index: int
    ) -> GroupData:
        return GroupData(
            indices=group.indices + [index],
            merged_tree=self.comparator.merge(group.merged_tree, structure.tree),
        )
