from typing import Any

from faker import Faker

from src.bl.generator.strategies.base import ValueGenerationStrategy
from src.core.pattern_registry import FIELD_NAME_MAPPINGS


class FieldNameStrategy(ValueGenerationStrategy):
    def __init__(self, faker: Faker):
        self.faker = faker

    def can_generate(self, field_name: str, field_schema: dict[str, Any]) -> bool:
        return True

    def generate(self, field_name: str, field_schema: dict[str, Any]) -> Any | None:
        field_lower = field_name.lower()

        for mapping in FIELD_NAME_MAPPINGS:
            if mapping.match_all:
                matches = all(kw in field_lower for kw in mapping.keywords)
            else:
                matches = any(kw in field_lower for kw in mapping.keywords)

            if matches:
                value = mapping.generator(self.faker)
                return self._enforce_string_length(value, field_schema)

        return self._enforce_string_length(self.faker.word(), field_schema)

    def _enforce_string_length(self, value: Any, field_schema: dict[str, Any]) -> Any:
        if not isinstance(value, str):
            return value
        min_len = field_schema.get("minLength")
        max_len = field_schema.get("maxLength")
        if max_len is not None and len(value) > max_len:
            value = value[:max_len]
        if min_len is not None and len(value) < min_len:
            value += self.faker.lexify("?" * (min_len - len(value)))
        return value
