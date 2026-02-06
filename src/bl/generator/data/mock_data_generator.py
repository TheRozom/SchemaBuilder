import random
from typing import Any

from faker import Faker

from src.bl.generator.config import get_default_ranges
from src.bl.generator.strategies import (
    CompositionStrategy,
    EnumStrategy,
    FieldNameStrategy,
    PatternStrategy,
    TypeStrategy,
    ValueGenerationStrategy,
)
from src.core import get_logger


class MockDataGenerator:
    def __init__(self, locale: str = "en_US", seed: int | None = None):
        self.faker = Faker(locale)
        self._defaults = get_default_ranges()
        self.logger = get_logger(__name__)

        if seed is not None:
            Faker.seed(seed)
            random.seed(seed)

        self._setup_strategies()

    def _setup_strategies(self) -> None:
        field_name_strategy = FieldNameStrategy(self.faker)
        self.strategies: list[ValueGenerationStrategy] = [
            CompositionStrategy(self._generate_value),
            EnumStrategy(),
            PatternStrategy(self.faker),
            TypeStrategy(
                self.faker,
                field_name_strategy,
                self._generate_value,
                self._generate_single_record,
            ),
            field_name_strategy,
        ]

    def generate_from_schema(
        self, schema: dict[str, Any], count: int = 1
    ) -> dict[str, Any] | list[dict[str, Any]]:
        if count < 1:
            raise ValueError("count must be at least 1")
        if count > 10000:
            raise ValueError("count exceeds maximum allowed value of 10000")

        if count == 1:
            return self._generate_single_record(schema)
        return [self._generate_single_record(schema) for _ in range(count)]

    def _resolve_top_level_composition(self, schema: dict[str, Any]) -> dict[str, Any]:
        if "properties" in schema:
            return schema

        if "allOf" in schema:
            merged: dict[str, Any] = {}
            for sub in schema["allOf"]:
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

        for keyword in ("anyOf", "oneOf"):
            if keyword in schema:
                return random.choice(schema[keyword])

        return schema

    def _generate_single_record(self, schema: dict[str, Any]) -> dict[str, Any]:
        schema = self._resolve_top_level_composition(schema)
        record = {}
        properties = schema.get("properties", {})

        for field_name, field_schema in properties.items():
            record[field_name] = self._generate_value(field_name, field_schema)

        return record

    def _generate_value(self, field_name: str, field_schema: dict[str, Any]) -> Any:
        if field_schema.get("type") == "null":
            return None

        null_possible = self._null_is_possible(field_schema)

        for strategy in self.strategies:
            if strategy.can_generate(field_name, field_schema):
                value = strategy.generate(field_name, field_schema)
                if value is not None or field_schema.get("type") == "null" or null_possible:
                    return value

        return self.faker.word()

    @staticmethod
    def _null_is_possible(field_schema: dict[str, Any]) -> bool:
        for keyword in ("anyOf", "oneOf"):
            for sub in field_schema.get(keyword, []):
                if sub.get("type") == "null":
                    return True
        return False
