import random
from typing import Any, Dict, List, Optional

from faker import Faker

from src.bl.generator.config import get_default_ranges
from src.bl.generator.strategies.base import ValueGenerationStrategy


class TypeStrategy(ValueGenerationStrategy):
    def __init__(self, faker: Faker, field_name_strategy: "FieldNameStrategy" = None):
        self.faker = faker
        self.field_name_strategy = field_name_strategy
        self._defaults = get_default_ranges()

    def can_generate(self, field_name: str, field_schema: Dict[str, Any]) -> bool:
        return "type" in field_schema

    def generate(self, field_name: str, field_schema: Dict[str, Any]) -> Any:
        field_type = field_schema.get("type")

        if field_type == "null":
            return None
        elif field_type == "string":
            return self._generate_string(field_name, field_schema)
        elif field_type == "integer":
            return self._generate_integer(field_schema)
        elif field_type == "number":
            return self._generate_number(field_schema)
        elif field_type == "boolean":
            return random.choice([True, False])
        elif field_type == "array":
            return self._generate_array(field_name, field_schema)
        elif field_type == "object":
            return self._generate_object(field_schema)

        return None

    def _generate_string(self, field_name: str, field_schema: Dict[str, Any]) -> str:
        min_len = field_schema.get("minLength", self._defaults.string_min_length)
        max_len = field_schema.get("maxLength", self._defaults.string_max_length)

        if self.field_name_strategy:
            value = str(self.field_name_strategy.generate(field_name, field_schema))
        else:
            value = self.faker.word()

        if min_len > len(value):
            padding_needed = min_len - len(value)
            if padding_needed >= 5:
                value += self.faker.text(max_nb_chars=padding_needed)
            else:
                value += self.faker.lexify("?" * padding_needed)
        elif len(value) > max_len:
            value = value[:max_len]

        return value

    def _generate_integer(self, field_schema: Dict[str, Any]) -> int:
        minimum = field_schema.get("minimum", self._defaults.int_min)
        maximum = field_schema.get("maximum", self._defaults.int_max)

        if field_schema.get("exclusiveMinimum") is not None:
            minimum = field_schema["exclusiveMinimum"] + 1
        if field_schema.get("exclusiveMaximum") is not None:
            maximum = field_schema["exclusiveMaximum"] - 1

        return random.randint(minimum, maximum)

    def _generate_number(self, field_schema: Dict[str, Any]) -> float:
        minimum = field_schema.get("minimum", self._defaults.float_min)
        maximum = field_schema.get("maximum", self._defaults.float_max)

        if field_schema.get("exclusiveMinimum") is not None:
            minimum = field_schema["exclusiveMinimum"] + 0.01
        if field_schema.get("exclusiveMaximum") is not None:
            maximum = field_schema["exclusiveMaximum"] - 0.01

        return round(random.uniform(minimum, maximum), 2)

    def _generate_array(self, field_name: str, field_schema: Dict[str, Any]) -> List[Any]:
        items_schema = field_schema.get("items", {})
        min_items = field_schema.get("minItems", self._defaults.array_min_items)
        max_items = field_schema.get("maxItems", self._defaults.array_max_items)
        length = random.randint(min_items, max_items)

        if isinstance(items_schema, dict):
            from src.bl.generator.data.mock_data_generator import MockDataGenerator

            generator = MockDataGenerator()
            return [
                generator._generate_value(f"{field_name}_item", items_schema) for _ in range(length)
            ]
        elif isinstance(items_schema, list):
            from src.bl.generator.data.mock_data_generator import MockDataGenerator

            generator = MockDataGenerator()
            return [
                generator._generate_value(f"{field_name}_item_{i}", s)
                for i, s in enumerate(items_schema[:length])
            ]

        return [self.faker.word() for _ in range(length)]

    def _generate_object(self, field_schema: Dict[str, Any]) -> Dict[str, Any]:
        from src.bl.generator.data.mock_data_generator import MockDataGenerator

        generator = MockDataGenerator()
        return generator._generate_single_record(field_schema)
