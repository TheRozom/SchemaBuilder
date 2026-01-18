import pytest
from src.bl.scoring.scoring_engine import ScoringEngine


def test_perfect_score():
    engine = ScoringEngine()
    schema = {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "minLength": 1,
                "maxLength": 10,
                "pattern": ".*",
            },
            "age": {"type": "integer", "minimum": 0, "maximum": 100},
        },
        "additionalProperties": False,
    }
    result = engine.score(schema)
    assert result.total_score == 100.0
    assert result.breakdown["strictness"] == 100.0


def test_low_score_ambiguity():
    engine = ScoringEngine()
    schema = {
        "type": "array",
        "items": {"anyOf": [{"type": "string"}, {"type": "integer"}]},
    }
    result = engine.score(schema)
    # Ambiguity should be low because of anyOf
    assert result.breakdown["ambiguity"] < 100.0


def test_low_score_completeness():
    engine = ScoringEngine()
    schema = {
        "type": "integer"
        # Missing min/max
    }
    result = engine.score(schema)
    assert result.breakdown["completeness"] < 100.0
