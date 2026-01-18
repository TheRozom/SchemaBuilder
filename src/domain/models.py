from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field

from src.bl.scoring.engine.scoring_engine import ScoreResult


class ValidationResult(BaseModel):
    valid: bool = Field(..., description="Whether all data validates against the schema")
    total_errors: int = Field(..., description="Total number of validation errors")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="List of validation errors")


class ConflictAnalysis(BaseModel):
    total_objects: int = Field(..., description="Number of JSON objects analyzed")
    unique_structures: int = Field(..., description="Number of unique structural groups found")
    should_split_schemas: bool = Field(..., description="Whether schemas should be split")
    recommendation: str = Field(..., description="Recommendation message")
    confidence: str = Field(..., description="Confidence level: low, medium, high")


class SchemaDefinition(BaseModel):
    schema_content: Dict[str, Any] = Field(..., description="The generated JSON Schema")
    score: Optional[ScoreResult] = Field(None, description="Quality score of the schema")
    validation: Optional[ValidationResult] = Field(None, description="Validation results against input data")
    analysis: Optional[ConflictAnalysis] = Field(None, description="Structure analysis result (when built from multiple objects)")
