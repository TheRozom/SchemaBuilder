from enum import Enum


class TreeKeys(str, Enum):
    INDEX = "index"
    TREE = "tree"
    KEY_COUNT = "key_count"
    INDICES = "indices"
    MERGED_TREE = "merged_tree"
