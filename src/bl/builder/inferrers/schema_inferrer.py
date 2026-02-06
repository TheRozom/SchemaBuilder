from typing import Any, Dict, List

from src.bl.builder.config import PATTERN_REGISTRY
from src.bl.builder.mergers import SchemaMerger
from src.core import get_logger
from src.core.config import settings
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
        self.unknown_samples: Dict[str, List[str]] = {}

    def infer(self, data: Any, path: str = "") -> SchemaNode:
        logger.debug(
            "Inferring schema for path '%s', type: %s",
            path,
            get_type_name(data),
        )

        if is_none(data):
            return SchemaNode(type=SchemaType.NULL)

        if is_bool(data):
            return SchemaNode(type=SchemaType.BOOLEAN)

        if is_int(data):
            return SchemaNode(type=SchemaType.INTEGER, minimum=data, maximum=data)

        if is_float(data):
            return SchemaNode(type=SchemaType.NUMBER, minimum=0)

        if is_string(data):
            return self._infer_string(data, path)

        if is_list(data):
            return self._infer_array(data, path)

        if is_dict(data):
            return self._infer_object(data, path)

        logger.warning("Unknown data type at path '%s': %s", path, type(data).__name__)

        return SchemaNode()

    def _infer_string(self, data: str, path: str) -> SchemaNode:
        schema = SchemaNode(type=SchemaType.STRING, minLength=0, maxLength=len(data))

        matched = False

        for name, pattern in PATTERN_REGISTRY.items():
            if pattern.match(data):
                schema.pattern = pattern.pattern
                logger.debug("Matched pattern '%s' for path '%s'", name, path)
                matched = True
                break

        if not matched:
            if path not in self.unknown_samples:
                self.unknown_samples[path] = []

            max_samples = settings.INFERENCE_MAX_SAMPLES

            if (
                len(self.unknown_samples[path]) < max_samples
                and data not in self.unknown_samples[path]
            ):
                self.unknown_samples[path].append(data)

        return schema

    def _infer_array(self, data: List[Any], path: str) -> SchemaNode:
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

    def _infer_object(self, data: Dict[str, Any], path: str) -> SchemaNode:
        logger.debug("Inferring object schema at path '%s' with %d properties", path, len(data))

        return SchemaNode(
            type=SchemaType.OBJECT,
            properties={k: self.infer(v, f"{path}.{k}" if path else k) for k, v in data.items()},
            additionalProperties=False,
        )
