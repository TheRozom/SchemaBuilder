from pydantic import BaseModel, Field

from .validation_error import ValidationError


class ValidationResult(BaseModel):
    valid: bool
    total_errors: int = Field(default=0)
    errors: list[ValidationError] = Field(default_factory=list)
