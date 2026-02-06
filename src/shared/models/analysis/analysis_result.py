from typing import List

from pydantic import BaseModel

from .analysis_summary import AnalysisSummary
from .structure_group import StructureGroup


class AnalysisResult(BaseModel):
    objects_analyzed: int
    unique_structures: int
    groups: List[StructureGroup]
    similarity_matrix: List[List[float]]
    summary: AnalysisSummary
