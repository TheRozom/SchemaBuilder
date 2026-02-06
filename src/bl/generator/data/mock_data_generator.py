import random
from typing import Any, Dict, List, Optional, Union

from faker import Faker

from src.bl.generator.config import get_default_ranges
from src.bl.generator.strategies import (
    EnumStrategy,
    FieldNameStrategy,
    PatternStrategy,
    TypeStrategy,
    ValueGenerationStrategy,
)
from src.core import get_logger


class MockDataGenerator:
    """Generates mock data from JSON Schema definitions."""

    def __init__(self, locale: str = "en_US", seed: Optional[int] = None):
        self.faker = Faker(locale)
        self._defaults = get_default_ranges()
        self.logger = get_logger(__name__)

        if seed is not None:
            Faker.seed(seed)
            random.seed(seed)

        self._setup_strategies()

    def _setup_strategies(self) -> None:
        field_name_strategy = FieldNameStrategy(self.faker)
        self.strategies: List[ValueGenerationStrategy] = [
            EnumStrategy(),
            PatternStrategy(self.faker),
            TypeStrategy(self.faker, field_name_strategy),
            field_name_strategy,
        ]

    def generate_from_schema(
        self, schema: Dict[str, Any], count: int = 1
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        if count < 1:
            raise ValueError("count must be at least 1")
        if count > 10000:
            raise ValueError("count exceeds maximum allowed value of 10000")

        if count == 1:
            return self._generate_single_record(schema)
        return [self._generate_single_record(schema) for _ in range(count)]

    def _generate_single_record(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        record = {}
        properties = schema.get("properties", {})

        for field_name, field_schema in properties.items():
            record[field_name] = self._generate_value(field_name, field_schema)

        return record

    def _generate_value(self, field_name: str, field_schema: Dict[str, Any]) -> Any:
        if field_schema.get("type") == "null":
            return None

        for strategy in self.strategies:
            if strategy.can_generate(field_name, field_schema):
                value = strategy.generate(field_name, field_schema)
                if value is not None or field_schema.get("type") == "null":
                    return value

        return self.faker.word()
