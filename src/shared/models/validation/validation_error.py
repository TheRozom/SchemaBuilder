from typing import Any, List, Optional
from pydantic import BaseModel, Field


class ValidationError(BaseModel):
    """Single validation error with detailed fix information"""
    object_index: int
    path: str
    message: str
    validator: str
    failed_value: str

    # Detailed schema fix information
    schema_path: str = Field(default="", description="Path in the schema where the constraint is defined")
    expected_type: Optional[str] = Field(default=None, description="Type expected by schema")
    actual_type: str = Field(default="", description="Actual type of the value")
    constraint_name: Optional[str] = Field(default=None, description="Name of the failed constraint (e.g., minLength, pattern)")
    constraint_value: Optional[Any] = Field(default=None, description="Value of the constraint that failed")
    allowed_values: Optional[List[Any]] = Field(default=None, description="Allowed values if enum constraint failed")
    fix_suggestion: str = Field(default="", description="Specific suggestion on how to fix the schema")
