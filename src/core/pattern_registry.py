import random
import re
import string
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from re import Pattern
from typing import Any

from faker import Faker


@dataclass(frozen=True)
class PatternDefinition:
    name: str
    regex: Pattern[str]
    generator: Callable[[Faker], Any]
    priority: int
    constrained_generator: Callable[[Faker, int, int | None], str] | None = None


@dataclass(frozen=True)
class FieldNameMapping:
    keywords: list[str] = field(default_factory=list)
    match_all: bool = False
    generator: Callable[[Faker], Any] = field(default_factory=lambda: lambda f: f.word())


@dataclass(frozen=True)
class DefaultRanges:
    int_min: int = 0
    int_max: int = 100
    float_min: float = 0.0
    float_max: float = 100.0
    string_min_length: int = 1
    string_max_length: int = 100
    array_min_items: int = 1
    array_max_items: int = 5
    year_min: int = 1950
    year_max: int = field(default_factory=lambda: datetime.now().year)


def _build_url_constrained(faker: Faker, min_len: int, max_len: int | None) -> str:
    scheme = "http"
    tld = random.choice(["co", "io", "me", "com", "org", "net"])
    if max_len is None:
        max_len = 50
    available = max_len - len(scheme) - len("://") - len(".") - len(tld)
    domain_len = max(1, min(available, random.randint(2, 6)))
    domain = faker.lexify("?" * domain_len).lower()
    url = f"{scheme}://{domain}.{tld}"
    if len(url) < min_len:
        padding = min_len - len(url)
        url += "/" + faker.lexify("?" * (padding - 1)).lower()
    return url


def _build_email_constrained(faker: Faker, min_len: int, max_len: int | None) -> str:
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


def _build_word_constrained(faker: Faker, min_len: int, max_len: int | None) -> str:
    word = faker.word()
    if max_len is not None and len(word) > max_len:
        word = word[:max_len]
    if len(word) < min_len:
        word += faker.lexify("?" * (min_len - len(word)))
    return word


def _build_alphanumeric_constrained(faker: Faker, min_len: int, max_len: int | None) -> str:
    if max_len is None:
        max_len = 8
    length = random.randint(max(1, min_len), max_len)
    return faker.bothify("?" * length)


def _build_numbers_only_constrained(faker: Faker, min_len: int, max_len: int | None) -> str:
    if max_len is None:
        max_len = 4
    length = random.randint(max(1, min_len), max_len)
    return "".join(random.choices(string.digits, k=length))


PATTERN_REGISTRY: dict[str, PatternDefinition] = {
    "uuid": PatternDefinition(
        name="uuid",
        regex=re.compile(
            r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
        ),
        generator=lambda f: str(f.uuid4()),
        priority=100,
    ),
    "hex_color": PatternDefinition(
        name="hex_color",
        regex=re.compile(r"^#[0-9a-fA-F]{6}$"),
        generator=lambda f: str(f.hex_color()),
        priority=95,
    ),
    "email": PatternDefinition(
        name="email",
        regex=re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"),
        generator=lambda f: f.email(),
        priority=90,
        constrained_generator=_build_email_constrained,
    ),
    "datetime": PatternDefinition(
        name="datetime",
        regex=re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?$"),
        generator=lambda f: str(f.iso8601()),
        priority=90,
    ),
    "credit_card": PatternDefinition(
        name="credit_card",
        regex=re.compile(r"^\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}$"),
        generator=lambda f: f.credit_card_number(),
        priority=85,
    ),
    "ipv4": PatternDefinition(
        name="ipv4",
        regex=re.compile(r"^(\d{1,3}\.){3}\d{1,3}$"),
        generator=lambda f: f.ipv4(),
        priority=80,
    ),
    "date": PatternDefinition(
        name="date",
        regex=re.compile(r"^\d{4}-\d{2}-\d{2}$"),
        generator=lambda f: str(f.date()),
        priority=80,
    ),
    "phone_us": PatternDefinition(
        name="phone_us",
        regex=re.compile(r"^\+?1?\s*\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})$"),
        generator=lambda f: f.phone_number(),
        priority=80,
    ),
    "zipcode_us": PatternDefinition(
        name="zipcode_us",
        regex=re.compile(r"^\d{5}(-\d{4})?$"),
        generator=lambda f: f.zipcode(),
        priority=80,
    ),
    "url": PatternDefinition(
        name="url",
        regex=re.compile(r"^https?://[^\s]+$"),
        generator=lambda f: f.url(),
        priority=70,
        constrained_generator=_build_url_constrained,
    ),
    "date_us": PatternDefinition(
        name="date_us",
        regex=re.compile(r"^\d{1,2}/\d{1,2}/\d{2,4}$"),
        generator=lambda f: str(f.date(pattern="%m/%d/%Y")),
        priority=70,
    ),
    "time": PatternDefinition(
        name="time",
        regex=re.compile(r"^\d{1,2}:\d{2}(:\d{2})?(\s?(AM|PM))?$", re.IGNORECASE),
        generator=lambda f: f.time(),
        priority=60,
    ),
    "alphanumeric": PatternDefinition(
        name="alphanumeric",
        regex=re.compile(r"^[a-zA-Z0-9]+$"),
        generator=lambda f: f.bothify(text="????####"),
        priority=30,
        constrained_generator=_build_alphanumeric_constrained,
    ),
    "numbers_only": PatternDefinition(
        name="numbers_only",
        regex=re.compile(r"^[0-9]+$"),
        generator=lambda f: str(random.randint(1000, 9999)),
        priority=20,
        constrained_generator=_build_numbers_only_constrained,
    ),
    "english_words": PatternDefinition(
        name="english_words",
        regex=re.compile(r"^[A-Za-z ]+$", re.IGNORECASE),
        generator=lambda f: f.word(),
        priority=10,
        constrained_generator=_build_word_constrained,
    ),
    "phone_intl": PatternDefinition(
        name="phone_intl",
        regex=re.compile(r"^\+?[\d\s\-\(\)]+$"),
        generator=lambda f: f.phone_number(),
        priority=10,
    ),
}

_REGEX_TO_DEFINITION: dict[str, PatternDefinition] = {
    defn.regex.pattern: defn for defn in PATTERN_REGISTRY.values()
}


def get_definition_by_regex(regex_string: str) -> PatternDefinition | None:
    return _REGEX_TO_DEFINITION.get(regex_string)


_current_year = datetime.now().year

FIELD_NAME_MAPPINGS: list[FieldNameMapping] = [
    FieldNameMapping(
        keywords=["first", "name"], match_all=True, generator=lambda f: f.first_name()
    ),
    FieldNameMapping(keywords=["last", "name"], match_all=True, generator=lambda f: f.last_name()),
    FieldNameMapping(
        keywords=["middle", "name"], match_all=True, generator=lambda f: f.first_name()
    ),
    FieldNameMapping(keywords=["full", "name"], match_all=True, generator=lambda f: f.name()),
    FieldNameMapping(keywords=["name"], match_all=True, generator=lambda f: f.name()),
    FieldNameMapping(keywords=["street"], generator=lambda f: f.street_address()),
    FieldNameMapping(keywords=["state"], generator=lambda f: f.state()),
    FieldNameMapping(keywords=["province"], generator=lambda f: f.state()),
    FieldNameMapping(keywords=["city"], generator=lambda f: f.city()),
    FieldNameMapping(keywords=["country"], generator=lambda f: f.country()),
    FieldNameMapping(keywords=["zip", "postal"], generator=lambda f: f.postcode()),
    FieldNameMapping(keywords=["username", "user_name"], generator=lambda f: f.user_name()),
    FieldNameMapping(keywords=["password"], generator=lambda f: f.password()),
    FieldNameMapping(keywords=["email"], generator=lambda f: f.email()),
    FieldNameMapping(keywords=["age"], generator=lambda f: random.randint(18, 80)),
    FieldNameMapping(keywords=["year"], generator=lambda f: random.randint(1950, _current_year)),
    FieldNameMapping(keywords=["month"], generator=lambda f: random.randint(1, 12)),
    FieldNameMapping(keywords=["day"], generator=lambda f: random.randint(1, 28)),
    FieldNameMapping(
        keywords=["title"],
        generator=lambda f: f.sentence(nb_words=4).rstrip("."),
    ),
    FieldNameMapping(
        keywords=["comment", "note", "description"],
        generator=lambda f: f.sentence(nb_words=10),
    ),
    FieldNameMapping(
        keywords=["code"],
        generator=lambda f: f.bothify(text="??####"),
    ),
]

DEFAULT_RANGES: DefaultRanges = DefaultRanges()
