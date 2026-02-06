import random
from typing import Any

from src.bl.generator.strategies.base import ValueGenerationStrategy


class EnumStrategy(ValueGenerationStrategy):
    def can_generate(self, field_name: str, field_schema: dict[str, Any]) -> bool:
        return "enum" in field_schema and field_schema["enum"]

    def generate(self, field_name: str, field_schema: dict[str, Any]) -> Any | None:
        enum_values = field_schema.get("enum")
        if enum_values:
            return random.choice(enum_values)
        return None
