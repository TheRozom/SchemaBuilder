from typing import Any, Dict, Optional

from pydantic import BaseModel

from src.core import get_logger
from src.bl.scoring.rules.strictness import StrictnessRule
from src.bl.scoring.rules.completeness import CompletenessRule
from src.bl.scoring.rules.ambiguity import AmbiguityRule
from src.bl.scoring.rules.security import SecurityRule
from src.bl.scoring.config import ScoringWeights
from src.shared.exceptions import ScoringError, InputValidationError

logger = get_logger(__name__)


class ScoreResult(BaseModel):
    total_score: float
    ai_score: Optional[int] = None
    breakdown: Dict[str, float]

    @property
    def overall(self) -> int:
        return int(self.total_score)


class ScoringEngine:

    def __init__(self):
        self.security_rule = SecurityRule()
        self.rules = {
            "strictness": StrictnessRule(),
            "completeness": CompletenessRule(),
            "ambiguity": AmbiguityRule(),
            "security": self.security_rule,
        }
        self.weights = {
            "strictness": ScoringWeights.STRICTNESS,
            "completeness": ScoringWeights.COMPLETENESS,
            "ambiguity": ScoringWeights.AMBIGUITY,
            "security": ScoringWeights.SECURITY,
        }
        logger.debug("ScoringEngine initialized with %d rules", len(self.rules))

    def score(self, schema: Dict[str, Any]) -> ScoreResult:
        logger.debug("Scoring schema")

        if not isinstance(schema, dict):
            raise InputValidationError(
                message="Schema must be a dictionary",
                field="schema",
                expected_type="dict",
            )

        if not schema:
            raise InputValidationError(
                message="Schema cannot be empty",
                field="schema",
            )

        try:
            scores = {}
            total = 0.0

            for name, rule in self.rules.items():
                s = rule.evaluate(schema)
                scores[name] = round(s * 100, 2)
                total += s * self.weights[name]
                logger.debug("Rule '%s': %.2f", name, scores[name])

            if self.security_rule.score_zero:
                logger.warning("Security rule failed, setting total score to 0")
                total = 0.0

            result = ScoreResult(total_score=round(total * 100, 2), breakdown=scores)

            logger.info(
                "Schema scored: total=%.2f, breakdown=%s", result.total_score, scores
            )
            return result

        except Exception as e:
            logger.error("Scoring failed: %s", e)
            raise ScoringError(
                message=f"Failed to score schema: {e}",
            ) from e
