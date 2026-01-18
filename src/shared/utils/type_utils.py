from typing import Any, List, Optional, Type, Union


class TypeChecker:

    @staticmethod
    def is_dict(value: Any) -> bool:
        return isinstance(value, dict)

    @staticmethod
    def is_list(value: Any) -> bool:
        return isinstance(value, list)

    @staticmethod
    def is_string(value: Any) -> bool:
        return isinstance(value, str)

    @staticmethod
    def is_int(value: Any) -> bool:
        return isinstance(value, int) and not isinstance(value, bool)

    @staticmethod
    def is_float(value: Any) -> bool:
        return isinstance(value, float)

    @staticmethod
    def is_bool(value: Any) -> bool:
        return isinstance(value, bool)

    @staticmethod
    def is_none(value: Any) -> bool:
        return value is None

    @staticmethod
    def is_numeric(value: Any) -> bool:
        return TypeChecker.is_int(value) or TypeChecker.is_float(value)

    @staticmethod
    def is_primitive(value: Any) -> bool:
        return not TypeChecker.is_dict(value) and not TypeChecker.is_list(value)

    @staticmethod
    def is_empty_collection(value: Any) -> bool:
        if TypeChecker.is_dict(value):
            return len(value) == 0
        if TypeChecker.is_list(value):
            return len(value) == 0
        return False

    @staticmethod
    def is_list_of_dicts(value: Any) -> bool:
        return (
            TypeChecker.is_list(value)
            and len(value) > 0
            and TypeChecker.is_dict(value[0])
        )

    @staticmethod
    def get_type_name(value: Any) -> str:
        if TypeChecker.is_none(value):
            return "null"
        if TypeChecker.is_bool(value):
            return "boolean"
        if TypeChecker.is_int(value):
            return "integer"
        if TypeChecker.is_float(value):
            return "number"
        if TypeChecker.is_string(value):
            return "string"
        if TypeChecker.is_list(value):
            return "array"
        if TypeChecker.is_dict(value):
            return "object"
        return type(value).__name__

    @staticmethod
    def safe_len(value: Any) -> int:
        try:
            return len(value)
        except TypeError:
            return 0
