import random
from typing import Any, Dict, List, Optional, Union

from faker import Faker

from src.bl.generator.config import (
    get_default_ranges,
    get_field_name_keywords,
    get_pattern_generators,
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

    def generate_from_schema(
        self, schema: Dict[str, Any], count: int = 1
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Generate mock data from a JSON Schema."""
        # Validate count parameter to prevent memory/performance issues
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
        field_type = field_schema.get("type")
        pattern = field_schema.get("pattern")
        enum = field_schema.get("enum")

        if enum:
            return random.choice(enum)

        if pattern:
            value = self._generate_by_regex(pattern)
            if value is not None:
                return value
            value = self._generate_by_pattern(pattern)
            if value is not None:
                return value

        if field_type == "string":
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
            return self._generate_single_record(field_schema)
        elif field_type == "null":
            return None

        return self._generate_by_field_name(field_name)

    def _generate_by_regex(self, pattern: str) -> Optional[str]:
        try:
            if hasattr(self.faker, "regex"):
                return self.faker.regex(pattern)
        except Exception as e:
            # Log failure but continue - regex generation is best-effort
            self.logger.debug("Failed to generate from regex pattern '%s': %s", pattern, e)
        return None

    def _generate_by_pattern(self, pattern: str) -> Optional[Any]:
        for config in get_pattern_generators():
            if config.get("pattern") == pattern:
                generator = config.get("generator")
                args = config.get("args", {})

                if generator == "random_digits":
                    return str(random.randint(args.get("min_val", 1000), args.get("max_val", 9999)))
                elif generator == "word":
                    return self.faker.word()
                elif generator == "bothify":
                    return self.faker.bothify(text=args.get("text", "????####"))
        return None

    def _generate_by_field_name(self, field_name: str) -> Any:
        field_lower = field_name.lower()

        for config in get_field_name_keywords():
            keywords = config.get("keywords", [])
            match_all = config.get("match_all", False)

            if match_all:
                matches = all(kw in field_lower for kw in keywords)
            else:
                matches = any(kw in field_lower for kw in keywords)

            if matches:
                generator = config.get("generator")
                if generator:
                    args = config.get("args", {})
                    if generator == "random_int":
                        return random.randint(args.get("min_val", 0), args.get("max_val", 100))
                    elif generator == "random_year":
                        return random.randint(self._defaults.year_min, self._defaults.year_max)

                faker_method = config.get("faker_method")
                if faker_method and hasattr(self.faker, faker_method):
                    method = getattr(self.faker, faker_method)
                    faker_args = config.get("faker_args", {})
                    result = method(**faker_args) if faker_args else method()
                    if config.get("post_process") == "strip_period" and isinstance(result, str):
                        result = result.rstrip(".")
                    return result

        return self.faker.word()

    def _generate_string(self, field_name: str, field_schema: Dict[str, Any]) -> str:
        min_len = field_schema.get("minLength", self._defaults.string_min_length)
        max_len = field_schema.get("maxLength", self._defaults.string_max_length)
        value = str(self._generate_by_field_name(field_name))

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
            return [self._generate_value(f"{field_name}_item", items_schema) for _ in range(length)]
        elif isinstance(items_schema, list):
            return [
                self._generate_value(f"{field_name}_item_{i}", s)
                for i, s in enumerate(items_schema[:length])
            ]

        return [self.faker.word() for _ in range(length)]
