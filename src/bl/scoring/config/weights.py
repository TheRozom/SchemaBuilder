from dataclasses import dataclass


@dataclass(frozen=True)
class ScoringWeights:
    STRICTNESS: float = 0.35
    COMPLETENESS: float = 0.35
    AMBIGUITY: float = 0.15
    SECURITY: float = 0.15
