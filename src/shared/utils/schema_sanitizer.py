from typing import Any


def strip_required_keywords(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: strip_required_keywords(item) for key, item in value.items() if key != "required"
        }
    if isinstance(value, list):
        return [strip_required_keywords(item) for item in value]
    return value
