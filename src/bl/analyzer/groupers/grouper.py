from typing import Any

from src.core.config_loader import load_yaml_config
from src.core.service_config import service_config
from src.shared.models import GroupData, JsonStructure

DEFAULT_SIMILARITY_THRESHOLD = 60


class Grouper:
    def __init__(self) -> None:
        self.comparator = service_config.tree_comparator
        config = load_yaml_config("grouper.yaml")
        self.similarity_threshold = (
            config.get("grouping", {}).get("similarity_threshold", DEFAULT_SIMILARITY_THRESHOLD)
        )

    def group_by_similarity(self, json_structures: list[JsonStructure]) -> list[GroupData]:
        groups: list[GroupData] = []
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
        json_structures: list[JsonStructure],
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

    def _are_structures_compatible(self, tree_a: dict[str, Any], tree_b: dict[str, Any]) -> bool:
        if self.comparator.contains(tree_a, tree_b) or self.comparator.contains(tree_b, tree_a):
            return True

        similarity = self.comparator.ted_similarity(tree_a, tree_b)
        return similarity >= self.similarity_threshold

    def _merge_structure_into_group(
        self, group: GroupData, structure: JsonStructure, index: int
    ) -> GroupData:
        return GroupData(
            indices=group.indices + [index],
            merged_tree=self.comparator.merge(group.merged_tree, structure.tree),
        )
