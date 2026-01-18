from typing import Any, Dict, List
from pydantic import BaseModel, Field
from .validation_error import ValidationError


class ValidationResult(BaseModel):
    """Result of validating data against a schema"""
    valid: bool
    total_errors: int = Field(default=0)
    errors: List[ValidationError] = Field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return self.model_dump()
