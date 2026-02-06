import random
from typing import Any, Dict, Optional

from faker import Faker

from src.bl.generator.config import get_pattern_generators
from src.bl.generator.strategies.base import ValueGenerationStrategy
from src.core import get_logger

logger = get_logger(__name__)


class PatternStrategy(ValueGenerationStrategy):
    def __init__(self, faker: Faker):
        self.faker = faker

    def can_generate(self, field_name: str, field_schema: Dict[str, Any]) -> bool:
        return "pattern" in field_schema and field_schema["pattern"]

    def generate(self, field_name: str, field_schema: Dict[str, Any]) -> Optional[Any]:
        pattern = field_schema.get("pattern")
        if not pattern:
            return None

        value = self._generate_by_regex(pattern)
        if value is not None:
            return value

        value = self._generate_by_pattern(pattern)
        if value is not None:
            return value

        return None

    def _generate_by_regex(self, pattern: str) -> Optional[str]:
        try:
            if hasattr(self.faker, "regex"):
                return self.faker.regex(pattern)
        except Exception as e:
            logger.debug("Failed to generate from regex pattern '%s': %s", pattern, e)
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
