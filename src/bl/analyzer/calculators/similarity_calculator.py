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
        if self.comparator.contains(first_tree, second_tree) or self.comparator.contains(
            second_tree, first_tree
        ):
            return 100.0

        return self.comparator.key_similarity(first_tree, second_tree)
