from typing import Any

from pydantic import BaseModel


class GroupData(BaseModel):
    indices: list[int]
    merged_tree: dict[str, Any]
