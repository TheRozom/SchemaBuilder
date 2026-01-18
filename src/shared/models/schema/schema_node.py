from typing import Any, Dict, List, Optional, Union
from src.shared.enums import SchemaType
from pydantic import BaseModel, Field


class SchemaNode(BaseModel):
    """Pydantic model for JSON Schema nodes with default values"""

    type: Optional[SchemaType] = None

    # String constraints
    pattern: Optional[str] = None
    minLength: Optional[int] = None
    maxLength: Optional[int] = None
    format: Optional[str] = None

    # Numeric constraints
    minimum: Optional[int] = None
    maximum: Optional[int] = None
    exclusiveMinimum: Optional[int] = None
    exclusiveMaximum: Optional[int] = None
    multipleOf: Optional[int] = None

    # Array constraints
    items: Optional[Union[Dict[str, Any], "SchemaNode"]] = None
    minItems: Optional[int] = None
    maxItems: Optional[int] = None
    uniqueItems: Optional[bool] = None

    # Object constraints
    properties: Dict[str, Union[Dict[str, Any], "SchemaNode"]] = Field(
        default_factory=dict
    )
    additionalProperties: Optional[bool] = None
    required: List[str] = Field(default_factory=list)

    # Composition keywords
    anyOf: List[Union[Dict[str, Any], "SchemaNode"]] = Field(default_factory=list)
    oneOf: List[Union[Dict[str, Any], "SchemaNode"]] = Field(default_factory=list)
    allOf: List[Union[Dict[str, Any], "SchemaNode"]] = Field(default_factory=list)

    # Metadata
    title: Optional[str] = None
    description: Optional[str] = None
    default: Optional[Any] = None
    enum: Optional[List[Any]] = None
    const: Optional[Any] = None

    class Config:
        extra = "allow"  # Allow additional fields not explicitly defined

    def to_dict(self) -> Dict[str, Any]:
        """Convert SchemaNode to a plain dictionary, excluding None values"""
        result = {}
        for field_name, field_value in self:
            if field_value is None:
                continue

            # Skip empty lists
            if isinstance(field_value, list) and len(field_value) == 0:
                continue

            # Skip empty dicts
            if isinstance(field_value, dict) and len(field_value) == 0:
                continue

            # Convert nested SchemaNode objects
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
            else:
                result[field_name] = field_value

        return result


# Enable forward references
SchemaNode.model_rebuild()
