import re
from typing import Dict, Pattern

from src.core import get_logger, load_yaml_config
from src.shared.exceptions import ConfigurationError

logger = get_logger(__name__)


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
            logger.warning(
                "Skipping pattern '%s': invalid regex '%s' (error: %s). "
                "This pattern will be unavailable for schema inference.",
                pattern_name,
                regex,
                e,
            )

    total_defined = len(config.get("patterns", {}))
    skipped = total_defined - len(patterns)
    if skipped > 0:
        logger.warning(
            "Pattern loading incomplete: %d/%d patterns skipped due to invalid regex",
            skipped,
            total_defined,
        )
    logger.info("Loaded %d/%d patterns from configuration", len(patterns), total_defined)

    if total_defined > 0 and len(patterns) == 0:
        raise ConfigurationError(
            "All patterns failed to load from configuration",
            config_file="patterns.yaml",
        )

    return patterns


PATTERN_REGISTRY: Dict[str, Pattern[str]] = _load_patterns_from_yaml()
