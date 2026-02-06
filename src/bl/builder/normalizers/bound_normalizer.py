import math

from src.shared.enums import SchemaType
from src.shared.models import SchemaNode


class BoundNormalizer:
    def smart_maximum(self, value: int | float | None, padding: float = 0.0) -> int | float | None:
        if value is None:
            return None
        if value == 0:
            return 0
        padded = value * (1 + padding) if value > 0 else value * (1 - padding)
        return self._ceil_to_clean(padded, is_int=isinstance(value, int))

    def smart_minimum(self, value: int | float | None, padding: float = 0.0) -> int | float | None:
        if value is None:
            return None
        if value == 0:
            return 0
        padded = value * (1 - padding) if value > 0 else value * (1 + padding)
        return self._floor_to_clean(padded, is_int=isinstance(value, int))

    def normalize_bounds(self, node: SchemaNode) -> None:
        if node.type in (SchemaType.INTEGER, SchemaType.NUMBER):
            node.minimum = self.smart_minimum(node.minimum)
            node.maximum = self.smart_maximum(node.maximum)

        for prop_node in node.properties.values():
            if isinstance(prop_node, SchemaNode):
                self.normalize_bounds(prop_node)

        if isinstance(node.items, SchemaNode):
            self.normalize_bounds(node.items)

        for variant in node.anyOf:
            if isinstance(variant, SchemaNode):
                self.normalize_bounds(variant)

    def _compute_step(self, abs_value: float) -> float:
        if abs_value < 1:
            return 10 ** math.floor(math.log10(abs_value))
        if abs_value < 10:
            return 1
        if abs_value < 50:
            return 5
        if abs_value < 100:
            return 10
        return 10 ** math.floor(math.log10(abs_value))

    def _ceil_to_clean(self, value: int | float, is_int: bool = False) -> int | float:
        abs_val = abs(value)
        step = self._compute_step(abs_val)

        if value >= 0:
            result = math.ceil(value / step) * step
        else:
            result = -math.floor(abs_val / step) * step

        if is_int:
            return int(result)
        return self._clean_float(result, step)

    def _floor_to_clean(self, value: int | float, is_int: bool = False) -> int | float:
        abs_val = abs(value)
        step = self._compute_step(abs_val)

        if value >= 0:
            result = math.floor(value / step) * step
        else:
            result = -math.ceil(abs_val / step) * step

        if is_int:
            return int(result)
        return self._clean_float(result, step)

    @staticmethod
    def _clean_float(value: float, step: float) -> float:
        if step >= 1:
            return float(value)
        decimals = max(0, -math.floor(math.log10(step)))
        return round(value, decimals)
