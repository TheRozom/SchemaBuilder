from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

from src.core import get_logger, load_yaml_config

logger = get_logger(__name__)


@dataclass(frozen=True)
class DefaultRanges:
    """Default value ranges for data generation."""

    int_min: int
    int_max: int
    float_min: float
    float_max: float
    string_min_length: int
    string_max_length: int
    array_min_items: int
    array_max_items: int
    year_min: int
    year_max: int


def _load_config() -> Dict[str, Any]:
    return load_yaml_config("semantic_types.yaml")


def _load_pattern_generators() -> List[Dict[str, Any]]:
    config = _load_config()
    pattern_generators = config.get("pattern_generators", [])
    logger.info("Loaded %d pattern generators from configuration", len(pattern_generators))
    return pattern_generators


def _load_field_name_keywords() -> List[Dict[str, Any]]:
    config = _load_config()
    field_keywords = config.get("field_name_keywords", [])
    logger.info("Loaded %d field name keyword mappings from configuration", len(field_keywords))
    return field_keywords


PATTERN_GENERATORS: List[Dict[str, Any]] = _load_pattern_generators()
FIELD_NAME_KEYWORDS: List[Dict[str, Any]] = _load_field_name_keywords()


def get_pattern_generators() -> List[Dict[str, Any]]:
    return PATTERN_GENERATORS


def get_field_name_keywords() -> List[Dict[str, Any]]:
    return FIELD_NAME_KEYWORDS


def get_default_ranges() -> DefaultRanges:
    """Load default value ranges from YAML configuration."""
    config = _load_config()
    ranges = config.get("default_ranges", {})

    int_range = ranges.get("integer", {})
    float_range = ranges.get("number", {})
    string_range = ranges.get("string", {})
    array_range = ranges.get("array", {})
    year_range = ranges.get("year", {})

    return DefaultRanges(
        int_min=int_range.get("minimum", 0),
        int_max=int_range.get("maximum", 100),
        float_min=float_range.get("minimum", 0.0),
        float_max=float_range.get("maximum", 100.0),
        string_min_length=string_range.get("min_length", 1),
        string_max_length=string_range.get("max_length", 100),
        array_min_items=array_range.get("min_items", 1),
        array_max_items=array_range.get("max_items", 5),
        year_min=year_range.get("min_year", 1950),
        year_max=datetime.now().year,
    )
