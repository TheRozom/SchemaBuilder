from typing import Any, Dict, Optional

from pydantic import BaseModel

from src.bl.scoring.config import ScoringWeights
from src.bl.scoring.rules.ambiguity import AmbiguityRule
from src.bl.scoring.rules.base import IRule
from src.bl.scoring.rules.completeness import CompletenessRule
from src.bl.scoring.rules.security import SecurityRule
from src.bl.scoring.rules.strictness import StrictnessRule
from src.core import get_logger
from src.shared.exceptions import InputValidationError, ScoringError

logger = get_logger(__name__)


class ScoreResult(BaseModel):
    total_score: float
    ai_score: Optional[int] = None
    breakdown: Dict[str, float]

    @property
    def overall(self) -> int:
        return int(self.total_score)


class ScoringEngine:
    """
    Evaluates JSON Schema quality using weighted scoring rules.

    The engine applies multiple rules (strictness, completeness, ambiguity, security)
    to assess schema quality on a 0-100 scale. Each rule contributes a weighted score
    to the final result. Security violations can force the total score to 0.

    Attributes:
        rules: Dictionary of scoring rules to evaluate
        weights: Dictionary of weights for each rule (should sum to 1.0)
        security_rule: Reference to SecurityRule for zero-score enforcement

    Example:
        >>> engine = ScoringEngine()
        >>> result = engine.score({"type": "object", "properties": {...}})
        >>> print(result.overall)  # 0-100 score
    """

    def __init__(
        self,
        rules: Optional[Dict[str, IRule]] = None,
        weights: Optional[Dict[str, float]] = None,
    ):
        if rules is not None:
            self.rules = rules
            # Find the SecurityRule instance if present in the provided rules
            self.security_rule = next(
                (r for r in rules.values() if isinstance(r, SecurityRule)),
                None,
            )
        else:
            self.security_rule = SecurityRule()
            self.rules: Dict[str, IRule] = {
                "strictness": StrictnessRule(),
                "completeness": CompletenessRule(),
                "ambiguity": AmbiguityRule(),
                "security": self.security_rule,
            }

        if weights is not None:
            self.weights = weights
        else:
            scoring_weights = ScoringWeights()
            self.weights = {
                "strictness": scoring_weights.STRICTNESS,
                "completeness": scoring_weights.COMPLETENESS,
                "ambiguity": scoring_weights.AMBIGUITY,
                "security": scoring_weights.SECURITY,
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

            if self.security_rule and self.security_rule.score_zero:
                logger.warning("Security rule failed, setting total score to 0")

                total = 0.0

            result = ScoreResult(total_score=round(total * 100, 2), breakdown=scores)

            logger.info("Schema scored: total=%.2f, breakdown=%s", result.total_score, scores)

            return result

        except (ValueError, KeyError, RuntimeError) as e:
            # Catch expected errors during scoring (missing keys, invalid values, etc.)
            logger.error("Scoring failed: %s", e)
            raise ScoringError(
                message=f"Failed to score schema: {e}",
            ) from e
