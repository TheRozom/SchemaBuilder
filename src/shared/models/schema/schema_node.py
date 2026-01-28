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
    properties: Dict[str, Union[Dict[str, Any], "SchemaNode"]] = Field(
        default_factory=dict
    )
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
            if field_value is None:
                continue

            if isinstance(field_value, list) and len(field_value) == 0:
                continue

            if isinstance(field_value, dict) and len(field_value) == 0:
                continue

            if isinstance(field_value, SchemaNode):
                result[field_name] = field_value.to_dict()

            elif isinstance(field_value, dict):
                result[field_name] = {
                    k: v.to_dict() if isinstance(v, SchemaNode) else v
                    for k, v in field_value.items()
                }

            elif isinstance(field_value, list):
                result[field_name] = [
                    item.to_dict() if isinstance(item, SchemaNode) else item
                    for item in field_value
                ]

            elif isinstance(field_value, SchemaType):
                result[field_name] = field_value.value

            else:
                result[field_name] = field_value

        return result


SchemaNode.model_rebuild()
