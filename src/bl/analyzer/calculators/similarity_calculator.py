from typing import List

from src.shared.models import JsonStructure
from src.bl.analyzer.trees import TreeComparator


class SimilarityCalculator:

    def __init__(self) -> None:
        self.comparator = TreeComparator()

    def calculate(self, json_structures: List[JsonStructure]) -> List[List[float]]:
        n = len(json_structures)
        matrix = [[0.0] * n for _ in range(n)]

        for i in range(n):
            for j in range(n):
                if i == j:
                    matrix[i][j] = 100.0
                else:
                    tree_i = json_structures[i].tree
                    tree_j = json_structures[j].tree

                    keys_i = set(self.comparator.flatten(tree_i))
                    keys_j = set(self.comparator.flatten(tree_j))

                    if not keys_i and not keys_j:
                        similarity = 100.0
                    elif not keys_i or not keys_j:
                        similarity = 0.0
                    else:
                        if self.comparator.contains(tree_i, tree_j):
                            similarity = 100.0
                        elif self.comparator.contains(tree_j, tree_i):
                            similarity = 100.0
                        else:
                            intersection = len(keys_i & keys_j)
                            smaller_size = min(len(keys_i), len(keys_j))
                            similarity = round((intersection / smaller_size) * 100, 2)

                    matrix[i][j] = similarity

        return matrix
