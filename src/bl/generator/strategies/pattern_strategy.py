import re
from typing import Any

import rstr
from faker import Faker

from src.bl.generator.strategies.base import ValueGenerationStrategy
from src.core import get_logger
from src.core.pattern_registry import get_definition_by_regex

logger = get_logger(__name__)


MAX_LENGTH_RETRIES = 10


class PatternStrategy(ValueGenerationStrategy):
    def __init__(self, faker: Faker):
        self.faker = faker

    def can_generate(self, field_name: str, field_schema: dict[str, Any]) -> bool:
        return "pattern" in field_schema and field_schema["pattern"]

    def generate(self, field_name: str, field_schema: dict[str, Any]) -> Any | None:
        pattern = field_schema.get("pattern")
        if not pattern:
            return None

        min_len = field_schema.get("minLength")
        max_len = field_schema.get("maxLength")

        definition = get_definition_by_regex(pattern)

        if definition:
            last_value = None
            for _ in range(MAX_LENGTH_RETRIES):
                value = str(definition.generator(self.faker))
                if self._fits_length(value, min_len, max_len):
                    return value
                last_value = value

            if definition.constrained_generator:
                value = definition.constrained_generator(self.faker, min_len or 0, max_len)
                if self._matches_pattern(value, pattern):
                    return value

            return last_value

        last_value = None
        for _ in range(MAX_LENGTH_RETRIES):
            value = self._generate_by_regex(pattern)
            if value is None:
                return None
            if self._fits_length(value, min_len, max_len):
                return value
            last_value = value

        enforced = self._enforce_length(last_value, min_len, max_len)
        if enforced and self._matches_pattern(enforced, pattern):
            return enforced
        return last_value

    @staticmethod
    def _fits_length(value: str, min_len: int | None, max_len: int | None) -> bool:
        if min_len is not None and len(value) < min_len:
            return False
        if max_len is not None and len(value) > max_len:
            return False
        return True

    @staticmethod
    def _matches_pattern(value: str, pattern: str) -> bool:
        try:
            return re.search(pattern, value) is not None
        except re.error:
            return False

    def _enforce_length(
        self, value: str | None, min_len: int | None, max_len: int | None
    ) -> str | None:
        if value is None:
            return None
        if max_len is not None and len(value) > max_len:
            value = value[:max_len]
        if min_len is not None and len(value) < min_len:
            value += self.faker.lexify("?" * (min_len - len(value)))
        return value

    @staticmethod
    def _generate_by_regex(pattern: str) -> str | None:
        try:
            return rstr.xeger(pattern)
        except re.error as e:
            logger.debug("Failed to generate from regex pattern '%s': %s", pattern, e)
            return None
