import random
from typing import Any, Dict, Optional

from faker import Faker

from src.bl.generator.config import get_default_ranges, get_field_name_keywords
from src.bl.generator.strategies.base import ValueGenerationStrategy


class FieldNameStrategy(ValueGenerationStrategy):
    def __init__(self, faker: Faker):
        self.faker = faker
        self._defaults = get_default_ranges()

    def can_generate(self, field_name: str, field_schema: Dict[str, Any]) -> bool:
        return True

    def generate(self, field_name: str, field_schema: Dict[str, Any]) -> Optional[Any]:
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
