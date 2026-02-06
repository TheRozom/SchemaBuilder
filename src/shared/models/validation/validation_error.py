from typing import Any

from pydantic import BaseModel, Field


class ValidationError(BaseModel):
    object_index: int
    path: str
    message: str
    validator: str
    failed_value: str
    schema_path: str = Field(
        default="", description="Path in the schema where the constraint is defined"
    )

    expected_type: str | None = Field(default=None, description="Type expected by schema")
    actual_type: str = Field(default="", description="Actual type of the value")

    constraint_name: str | None = Field(
        default=None,
        description="Name of the failed constraint (e.g., minLength, pattern)",
    )
    constraint_value: Any | None = Field(
        default=None, description="Value of the constraint that failed"
    )
    allowed_values: list[Any] | None = Field(
        default=None, description="Allowed values if enum constraint failed"
    )
    fix_suggestion: str = Field(
        default="", description="Specific suggestion on how to fix the schema"
    )
