from typing import Any

from pydantic import BaseModel, Field

from src.bl.scoring.engine.scoring_engine import ScoreResult


class ValidationResult(BaseModel):
    valid: bool = Field(..., description="Whether all data validates against the schema")
    total_errors: int = Field(..., description="Total number of validation errors")

    errors: list[dict[str, Any]] = Field(
        default_factory=list, description="List of validation errors"
    )


class ConflictAnalysis(BaseModel):
    total_objects: int = Field(..., description="Number of JSON objects analyzed")

    unique_structures: int = Field(..., description="Number of unique structural groups found")
    should_split_schemas: bool = Field(..., description="Whether schemas should be split")
    recommendation: str = Field(..., description="Recommendation message")
    confidence: str = Field(..., description="Confidence level: low, medium, high")


class SchemaDefinition(BaseModel):
    schema_content: dict[str, Any] = Field(..., description="The generated JSON Schema")

    score: ScoreResult | None = Field(None, description="Quality score of the schema")
    validation: ValidationResult | None = Field(
        None, description="Validation results against input data"
    )
    analysis: ConflictAnalysis | None = Field(
        None, description="Structure analysis result (when built from multiple objects)"
    )


class ReconcileSchemaResponse(BaseModel):
    original_schema: dict[str, Any] = Field(..., description="Original input JSON Schema")
    adjusted_schema: dict[str, Any] = Field(..., description="Schema adjusted to fit the data")
    score_before: ScoreResult = Field(..., description="Schema quality score before adjustment")
    score_after: ScoreResult = Field(..., description="Schema quality score after adjustment")
    validation_before: ValidationResult = Field(
        ..., description="Validation results before schema adjustment"
    )
    validation_after: ValidationResult = Field(
        ..., description="Validation results after schema adjustment"
    )
