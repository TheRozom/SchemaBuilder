from typing import Any

from src.core.service_config import service_config
from src.shared.models import JsonStructure


class SimilarityCalculator:
    def __init__(self) -> None:
        self.comparator = service_config.tree_comparator

    def calculate(self, json_structures: list[JsonStructure]) -> list[list[float]]:
        structure_count = len(json_structures)
        similarity_matrix = self._initialize_matrix(structure_count)

        for first_index in range(structure_count):
            for second_index in range(structure_count):
                if first_index == second_index:
                    similarity_matrix[first_index][second_index] = 100.0
                else:
                    similarity = self._calculate_similarity(
                        json_structures[first_index].tree,
                        json_structures[second_index].tree,
                    )
                    similarity_matrix[first_index][second_index] = similarity

        return similarity_matrix

    def _initialize_matrix(self, size: int) -> list[list[float]]:
        return [[0.0] * size for _ in range(size)]

    def _calculate_similarity(
        self, first_tree: dict[str, Any], second_tree: dict[str, Any]
    ) -> float:
        first_keys = set(self.comparator.flatten(first_tree))
        second_keys = set(self.comparator.flatten(second_tree))

        if self._both_empty(first_keys, second_keys):
            return 100.0

        if self._one_empty(first_keys, second_keys):
            return 0.0

        if self._has_containment(first_tree, second_tree):
            return 100.0

        return self._calculate_partial_similarity(first_keys, second_keys)

    def _both_empty(self, first_keys: set[str], second_keys: set[str]) -> bool:
        return not first_keys and not second_keys

    def _one_empty(self, first_keys: set[str], second_keys: set[str]) -> bool:
        return not first_keys or not second_keys

    def _has_containment(self, first_tree: dict[str, Any], second_tree: dict[str, Any]) -> bool:
        return self.comparator.contains(first_tree, second_tree) or self.comparator.contains(
            second_tree, first_tree
        )

    def _calculate_partial_similarity(self, first_keys: set[str], second_keys: set[str]) -> float:
        intersection_count = len(first_keys & second_keys)
        smaller_key_count = min(len(first_keys), len(second_keys))
        if smaller_key_count == 0:
            return 0.0
        return round((intersection_count / smaller_key_count) * 100, 2)
