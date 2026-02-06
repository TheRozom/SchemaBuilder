from typing import Any, List

from pydantic import BaseModel


class StructureGroup(BaseModel):
    group_id: int
    object_indices: List[int]
    merged_keys: List[str]
    key_count: int
    sample: Any
