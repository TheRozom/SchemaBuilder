from typing import Any

from pydantic import BaseModel

from src.core import get_logger
from src.core.service_config import service_config
from src.shared.exceptions import InputValidationError, ScoringError

logger = get_logger(__name__)


class ScoreResult(BaseModel):
    total_score: float
    breakdown: dict[str, float]

    @property
    def overall(self) -> int:
        return int(self.total_score)


class ScoringEngine:
    def __init__(self):
        self.registry = service_config.scoring_rule_registry
        self.rules = self.registry.get_enabled_rules()
        self.weights = self.registry.get_weights()
        self.security_rule = self.registry.get_security_rule()
        logger.debug("ScoringEngine initialized with %d rules", len(self.rules))

    def score(self, schema: dict[str, Any]) -> ScoreResult:
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
            logger.error("Scoring failed: %s", e)
            raise ScoringError(
                message=f"Failed to score schema: {e}",
            ) from e
