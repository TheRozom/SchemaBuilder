from typing import Any, Dict, List

from pydantic import BaseModel


class GroupData(BaseModel):
    indices: List[int]
    merged_tree: Dict[str, Any]
