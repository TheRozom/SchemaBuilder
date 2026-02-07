import random
import string
from typing import Any

from faker import Faker

from src.bl.generator.config import get_pattern_generators
from src.bl.generator.strategies.base import ValueGenerationStrategy
from src.core import get_logger

logger = get_logger(__name__)


MAX_LENGTH_RETRIES = 10

CONSTRAINED_BUILDERS = {
    r"^https?://[^\s]+$": "_build_url",
    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$": "_build_email",
    r"^[A-Za-z ]+$": "_build_word",
    r"^[a-zA-Z]+$": "_build_word",
}


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

        last_value = None
        for _ in range(MAX_LENGTH_RETRIES):
            value = self._generate_by_regex(pattern)
            if value is None:
                value = self._generate_by_pattern(pattern)
            if value is None:
                return None
            if self._fits_length(value, min_len, max_len):
                return value
            last_value = value

        constrained = self._build_constrained(pattern, min_len or 0, max_len)
        if constrained is not None:
            return constrained

        return last_value

    @staticmethod
    def _fits_length(value: str, min_len: int | None, max_len: int | None) -> bool:
        if min_len is not None and len(value) < min_len:
            return False
        if max_len is not None and len(value) > max_len:
            return False
        return True

    def _build_constrained(self, pattern: str, min_len: int, max_len: int | None) -> str | None:
        builder_name = CONSTRAINED_BUILDERS.get(pattern)
        if builder_name and hasattr(self, builder_name):
            return getattr(self, builder_name)(min_len, max_len)
        return None

    def _build_url(self, min_len: int, max_len: int | None) -> str:
        scheme = "http"
        tld = random.choice(["co", "io", "me", "com", "org", "net"])
        if max_len is None:
            max_len = 50
        available = max_len - len(scheme) - len("://") - len(".") - len(tld)
        domain_len = max(1, min(available, random.randint(2, 6)))
        domain = self.faker.lexify("?" * domain_len).lower()
        url = f"{scheme}://{domain}.{tld}"
        if len(url) < min_len:
            padding = min_len - len(url)
            url += "/" + self.faker.lexify("?" * (padding - 1)).lower()
        return url

    def _build_email(self, min_len: int, max_len: int | None) -> str:
        if max_len is None:
            max_len = 50
        tlds = [("co", 2), ("io", 2), ("me", 2), ("com", 3), ("org", 3)]
        random.shuffle(tlds)
        for tld, _tld_len in tlds:
            suffix = f"@a.{tld}"
            local_budget = max_len - len(suffix)
            if local_budget < 1:
                continue
            local_len = max(1, min(local_budget, random.randint(2, 5)))
            local = "".join(random.choices(string.ascii_lowercase + string.digits, k=local_len))
            email = f"{local}{suffix}"
            if len(email) >= min_len:
                return email
        return "a@b.co"

    def _build_word(self, min_len: int, max_len: int | None) -> str:
        word = self.faker.word()
        if max_len is not None and len(word) > max_len:
            word = word[:max_len]
        if len(word) < min_len:
            word += self.faker.lexify("?" * (min_len - len(word)))
        return word

    def _generate_by_regex(self, pattern: str) -> str | None:
        try:
            if hasattr(self.faker, "regex"):
                return self.faker.regex(pattern)
        except Exception as e:
            logger.debug("Failed to generate from regex pattern '%s': %s", pattern, e)
        return None

    def _generate_by_pattern(self, pattern: str) -> Any | None:
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
                elif generator == "faker":
                    method = args.get("method")
                    if method and hasattr(self.faker, method):
                        faker_args = args.get("faker_args", {})
                        return str(getattr(self.faker, method)(**faker_args))
        return None
