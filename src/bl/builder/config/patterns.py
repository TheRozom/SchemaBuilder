from re import Pattern

from src.core.pattern_registry import PATTERN_REGISTRY as _CORE_REGISTRY

PATTERN_REGISTRY: dict[str, Pattern[str]] = {
    name: defn.regex for name, defn in _CORE_REGISTRY.items()
}
