from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

from src.shared.enums import SchemaType


class SchemaNode(BaseModel):
    model_config = ConfigDict(extra="allow")
    type: Optional[SchemaType] = None
    pattern: Optional[str] = None
    minLength: Optional[int] = None
    maxLength: Optional[int] = None
    format: Optional[str] = None
    minimum: Optional[int] = None
    maximum: Optional[int] = None
    exclusiveMinimum: Optional[int] = None
    exclusiveMaximum: Optional[int] = None
    multipleOf: Optional[int] = None
    items: Optional[Union[Dict[str, Any], "SchemaNode"]] = None
    minItems: Optional[int] = None
    maxItems: Optional[int] = None
    uniqueItems: Optional[bool] = None
    properties: Dict[str, Union[Dict[str, Any], "SchemaNode"]] = Field(default_factory=dict)
    additionalProperties: Optional[bool] = None
    required: List[str] = Field(default_factory=list)
    anyOf: List[Union[Dict[str, Any], "SchemaNode"]] = Field(default_factory=list)

    oneOf: List[Union[Dict[str, Any], "SchemaNode"]] = Field(default_factory=list)

    allOf: List[Union[Dict[str, Any], "SchemaNode"]] = Field(default_factory=list)

    title: Optional[str] = None
    description: Optional[str] = None
    default: Optional[Any] = None
    enum: Optional[List[Any]] = None
    const: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {}

        for field_name, field_value in self:
            if self._is_empty(field_value):
                continue

            result[field_name] = self._serialize_value(field_value)

        return result

    @staticmethod
    def _is_empty(value: Any) -> bool:
        """Check if a value should be omitted from the serialized output."""
        if value is None:
            return True
        if isinstance(value, (list, dict)) and not value:
            return True
        return False

    @staticmethod
    def _serialize_value(value: Any) -> Any:
        """Serialize a single field value to a JSON-compatible type."""
        if isinstance(value, SchemaNode):
            return value.to_dict()

        if isinstance(value, dict):
            return {k: v.to_dict() if isinstance(v, SchemaNode) else v for k, v in value.items()}

        if isinstance(value, list):
            return [item.to_dict() if isinstance(item, SchemaNode) else item for item in value]

        if isinstance(value, SchemaType):
            return value.value

        return value


SchemaNode.model_rebuild()
