from typing import Any, Dict

from pydantic import BaseModel


class JsonStructure(BaseModel):
    index: int
    tree: Dict[str, Any]
    key_count: int
