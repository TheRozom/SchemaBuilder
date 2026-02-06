from pydantic import BaseModel

from .analysis_summary import AnalysisSummary
from .structure_group import StructureGroup


class AnalysisResult(BaseModel):
    objects_analyzed: int
    unique_structures: int
    groups: list[StructureGroup]
    similarity_matrix: list[list[float]]
    summary: AnalysisSummary
