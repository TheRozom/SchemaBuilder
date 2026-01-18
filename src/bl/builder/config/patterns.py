import re
from typing import Dict, Pattern
from enum import Enum

from src.core import get_logger, load_yaml_config

logger = get_logger(__name__)


class PatternType(str, Enum):
    EMAIL = "email"
    UUID = "uuid"
    IPV4 = "ipv4"
    DATE = "date"
    DATETIME = "datetime"


def _load_patterns_from_yaml() -> Dict[str, Pattern[str]]:
    config = load_yaml_config("patterns.yaml")

    patterns: Dict[str, Pattern[str]] = {}
    for pattern_name, pattern_config in config.get("patterns", {}).items():
        regex = pattern_config.get("regex", "")
        flags = pattern_config.get("flags", [])

        re_flags = 0
        for flag in flags:
            if flag == "IGNORECASE":
                re_flags |= re.IGNORECASE

        try:
            patterns[pattern_name] = re.compile(regex, re_flags)
            logger.debug("Loaded pattern '%s'", pattern_name)
        except re.error as e:
            logger.error("Invalid regex for pattern '%s': %s", pattern_name, e)

    logger.info("Loaded %d patterns from configuration", len(patterns))
    return patterns


PATTERN_REGISTRY: Dict[str, Pattern[str]] = _load_patterns_from_yaml()
