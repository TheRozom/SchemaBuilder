from pydantic import BaseModel
from src.shared.enums import ConfidenceLevel


class AnalysisSummary(BaseModel):
    total_objects: int
    unique_structures: int
    should_split_schemas: bool
    recommendation: str
    confidence: ConfidenceLevel
