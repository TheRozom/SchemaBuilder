from typing import Any


def is_dict(value: Any) -> bool:
    return isinstance(value, dict)


def is_list(value: Any) -> bool:
    return isinstance(value, list)


def is_string(value: Any) -> bool:
    return isinstance(value, str)


def is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def is_float(value: Any) -> bool:
    return isinstance(value, float)


def is_bool(value: Any) -> bool:
    return isinstance(value, bool)


def is_none(value: Any) -> bool:
    return value is None


def is_numeric(value: Any) -> bool:
    return is_int(value) or is_float(value)


def is_primitive(value: Any) -> bool:
    return not is_dict(value) and not is_list(value)


def is_empty_collection(value: Any) -> bool:
    if is_dict(value):
        return len(value) == 0

    if is_list(value):
        return len(value) == 0

    return False


def is_list_of_dicts(value: Any) -> bool:
    return is_list(value) and len(value) > 0 and all(is_dict(item) for item in value)


def get_type_name(value: Any) -> str:
    if is_none(value):
        return "null"

    if is_bool(value):
        return "boolean"

    if is_int(value):
        return "integer"

    if is_float(value):
        return "number"

    if is_string(value):
        return "string"

    if is_list(value):
        return "array"

    if is_dict(value):
        return "object"

    return type(value).__name__


def safe_len(value: Any) -> int:
    try:
        return len(value)

    except TypeError:
        return 0
