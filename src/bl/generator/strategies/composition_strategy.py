import random
from typing import Any, Callable, Dict, Optional

from src.bl.generator.strategies.base import ValueGenerationStrategy

COMPOSITION_KEYWORDS = ("anyOf", "oneOf", "allOf")


class CompositionStrategy(ValueGenerationStrategy):
    def __init__(self, generate_value: Callable[[str, Dict[str, Any]], Any]):
        self._generate_value = generate_value

    def can_generate(self, field_name: str, field_schema: Dict[str, Any]) -> bool:
        return any(kw in field_schema for kw in COMPOSITION_KEYWORDS)

    def generate(self, field_name: str, field_schema: Dict[str, Any]) -> Optional[Any]:
        if "allOf" in field_schema:
            merged = self._merge_all_of(field_schema["allOf"])
            return self._generate_value(field_name, merged)

        sub_schemas = field_schema.get("anyOf") or field_schema.get("oneOf", [])
        if sub_schemas:
            chosen = random.choice(sub_schemas)
            return self._generate_value(field_name, chosen)

        return None

    def _merge_all_of(self, sub_schemas: list) -> Dict[str, Any]:
        merged: Dict[str, Any] = {}
        for sub in sub_schemas:
            for key, value in sub.items():
                if key == "properties":
                    merged.setdefault("properties", {}).update(value)
                elif key == "required":
                    existing = set(merged.get("required", []))
                    existing.update(value)
                    merged["required"] = list(existing)
                else:
                    merged[key] = value
        return merged
