from typing import Any

from pydantic import BaseModel


class JsonStructure(BaseModel):
    index: int
    tree: dict[str, Any]
    key_count: int
