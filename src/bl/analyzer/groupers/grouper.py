from typing import List

from src.shared.models import JsonStructure, GroupData
from src.bl.analyzer.trees import TreeComparator


class Grouper:

    def __init__(self) -> None:
        self.comparator = TreeComparator()

    def group_by_containment(
        self, json_structures: List[JsonStructure]
    ) -> List[GroupData]:
        groups: List[GroupData] = []
        used_indices = set()

        for i, struct_i in enumerate(json_structures):
            if i in used_indices:
                continue

            group = GroupData(indices=[i], merged_tree=struct_i.tree)
            used_indices.add(i)

            for j, struct_j in enumerate(json_structures[i + 1 :], start=i + 1):
                if j in used_indices:
                    continue

                tree_i = group.merged_tree
                tree_j = struct_j.tree

                if self.comparator.contains(tree_i, tree_j) or self.comparator.contains(
                    tree_j, tree_i
                ):
                    group.indices.append(j)
                    group.merged_tree = self.comparator.merge(tree_i, tree_j)
                    used_indices.add(j)

            groups.append(group)

        return groups
