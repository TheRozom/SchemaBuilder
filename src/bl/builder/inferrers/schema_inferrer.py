from collections.abc import Callable
from typing import Any

from src.bl.builder.mergers import SchemaMerger
from src.core import get_logger
from src.core.config import settings
from src.core.pattern_registry import PATTERN_REGISTRY
from src.shared.models import SchemaNode, SchemaType
from src.shared.utils import (
    get_type_name,
    is_bool,
    is_dict,
    is_float,
    is_int,
    is_list,
    is_none,
    is_string,
)

logger = get_logger(__name__)


class SchemaInferrer:
    def __init__(self):
        self.unknown_samples: dict[str, list[str]] = {}
        self._type_handlers = self._build_type_registry()

    def _build_type_registry(
        self,
    ) -> list[tuple[Callable[[Any], bool], Callable[[Any, str], SchemaNode]]]:
        return [
            (is_none, self._handle_none),
            (is_bool, self._handle_bool),
            (is_int, self._handle_int),
            (is_float, self._handle_float),
            (is_string, self._infer_string),
            (is_list, self._infer_array),
            (is_dict, self._infer_object),
        ]

    def infer(self, data: Any, path: str = "") -> SchemaNode:
        logger.debug(
            "Inferring schema for path '%s', type: %s",
            path,
            get_type_name(data),
        )

        for predicate, handler in self._type_handlers:
            if predicate(data):
                return handler(data, path)

        logger.warning("Unknown data type at path '%s': %s", path, type(data).__name__)

        return SchemaNode()

    def _handle_none(self, data: None, path: str) -> SchemaNode:
        return SchemaNode(type=SchemaType.NULL)

    def _handle_bool(self, data: bool, path: str) -> SchemaNode:
        return SchemaNode(type=SchemaType.BOOLEAN)

    def _handle_int(self, data: int, path: str) -> SchemaNode:
        return SchemaNode(type=SchemaType.INTEGER, minimum=min(0, data), maximum=data)

    def _handle_float(self, data: float, path: str) -> SchemaNode:
        return SchemaNode(type=SchemaType.NUMBER, minimum=min(0, data), maximum=data)

    def _infer_string(self, data: str, path: str) -> SchemaNode:
        schema = SchemaNode(type=SchemaType.STRING, minLength=0, maxLength=len(data))

        matches = []

        for defn in PATTERN_REGISTRY.values():
            if defn.regex.match(data):
                matches.append(defn)

        if matches:
            best = max(matches, key=lambda d: d.priority)
            schema.pattern = best.regex.pattern
            logger.debug("Matched pattern '%s' for path '%s'", best.name, path)

        if not matches:
            if path not in self.unknown_samples:
                self.unknown_samples[path] = []

            max_samples = settings.INFERENCE_MAX_SAMPLES

            if (
                len(self.unknown_samples[path]) < max_samples
                and data not in self.unknown_samples[path]
            ):
                self.unknown_samples[path].append(data)

        return schema

    def _infer_array(self, data: list[Any], path: str) -> SchemaNode:
        schema = SchemaNode(type=SchemaType.ARRAY, minItems=0, maxItems=len(data))

        if not data:
            logger.debug("Empty array at path '%s'", path)

            return schema

        merger = SchemaMerger()
        first_item_schema = self.infer(data[0], path + "[]")
        merged_item_schema = first_item_schema

        for item in data[1:]:
            item_schema = self.infer(item, path + "[]")
            merged_item_schema = merger.merge(merged_item_schema, item_schema)

        schema.items = merged_item_schema

        return schema

    def _infer_object(self, data: dict[str, Any], path: str) -> SchemaNode:
        logger.debug("Inferring object schema at path '%s' with %d properties", path, len(data))

        return SchemaNode(
            type=SchemaType.OBJECT,
            properties={k: self.infer(v, f"{path}.{k}" if path else k) for k, v in data.items()},
            additionalProperties=False,
        )
