import random
from typing import Any, Dict, Optional

from src.bl.generator.strategies.base import ValueGenerationStrategy


class EnumStrategy(ValueGenerationStrategy):
    def can_generate(self, field_name: str, field_schema: Dict[str, Any]) -> bool:
        return "enum" in field_schema and field_schema["enum"]

    def generate(self, field_name: str, field_schema: Dict[str, Any]) -> Optional[Any]:
        enum_values = field_schema.get("enum")
        if enum_values:
            return random.choice(enum_values)
        return None
