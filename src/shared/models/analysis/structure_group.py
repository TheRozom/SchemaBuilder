from typing import Any

from pydantic import BaseModel


class StructureGroup(BaseModel):
    group_id: int
    object_indices: list[int]
    merged_keys: list[str]
    key_count: int
    sample: Any
