from typing import Any, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.shared.enums import SchemaType
from src.shared.utils import strip_required_keywords


class SchemaNode(BaseModel):
    model_config = ConfigDict(extra="allow")
    type: SchemaType | None = None
    pattern: str | None = None
    minLength: int | None = None
    maxLength: int | None = None
    format: str | None = None
    minimum: int | float | None = None
    maximum: int | float | None = None
    exclusiveMinimum: int | float | None = None
    exclusiveMaximum: int | float | None = None
    multipleOf: int | float | None = None
    items: Union[dict[str, Any], "SchemaNode"] | None = None
    minItems: int | None = None
    maxItems: int | None = None
    uniqueItems: bool | None = None
    properties: dict[str, Union[dict[str, Any], "SchemaNode"]] = Field(default_factory=dict)
    additionalProperties: bool | None = None
    anyOf: list[Union[dict[str, Any], "SchemaNode"]] = Field(default_factory=list)

    oneOf: list[Union[dict[str, Any], "SchemaNode"]] = Field(default_factory=list)

    allOf: list[Union[dict[str, Any], "SchemaNode"]] = Field(default_factory=list)

    title: str | None = None
    description: str | None = None
    default: Any | None = None
    enum: list[Any] | None = None
    const: Any | None = None

    @model_validator(mode="before")
    @classmethod
    def remove_required_keywords(cls, value: Any) -> Any:
        return strip_required_keywords(value)

    def to_dict(self) -> dict[str, Any]:
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
