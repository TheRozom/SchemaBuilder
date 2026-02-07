from src.core.pattern_registry import (
    DEFAULT_RANGES,
    FIELD_NAME_MAPPINGS,
    DefaultRanges,
    FieldNameMapping,
)


def get_default_ranges() -> DefaultRanges:
    return DEFAULT_RANGES


def get_field_name_keywords() -> list[FieldNameMapping]:
    return FIELD_NAME_MAPPINGS
