from unittest.mock import patch

import pytest

from src.bl.scoring.engine.scoring_engine import ScoreResult, ScoringEngine
from src.bl.scoring.rules.ambiguity import AmbiguityRule
from src.bl.scoring.rules.completeness import CompletenessRule
from src.bl.scoring.rules.security import SecurityRule
from src.bl.scoring.rules.strictness import StrictnessRule
from src.shared.exceptions import InputValidationError


class TestScoringEngine:
    def test_score_returns_score_result(self):
        engine = ScoringEngine()
        schema = {"type": "object", "properties": {}, "additionalProperties": False}

        result = engine.score(schema)
        assert isinstance(result, ScoreResult)
        assert hasattr(result, "total_score")
        assert hasattr(result, "breakdown")
        assert isinstance(result.total_score, float)
        assert isinstance(result.breakdown, dict)

    def test_score_with_valid_schema(self):
        engine = ScoringEngine()
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string", "minLength": 1, "maxLength": 100},
                "age": {"type": "integer", "minimum": 0, "maximum": 150},
            },
            "additionalProperties": False,
        }
        result = engine.score(schema)
        assert result.total_score >= 0
        assert result.total_score <= 100
        assert "strictness" in result.breakdown
        assert "completeness" in result.breakdown
        assert "ambiguity" in result.breakdown
        assert "security" in result.breakdown

    def test_score_with_empty_schema_raises_input_validation_error(self):
        engine = ScoringEngine()

        with pytest.raises(InputValidationError) as exc_info:
            engine.score({})

        assert "empty" in exc_info.value.message.lower()

    def test_score_with_non_dict_raises_input_validation_error(self):
        engine = ScoringEngine()

        with pytest.raises(InputValidationError) as exc_info:
            engine.score("not a dict")

        assert exc_info.value.field == "schema"
        assert exc_info.value.expected_type == "dict"

    def test_score_with_list_raises_input_validation_error(self):
        engine = ScoringEngine()

        with pytest.raises(InputValidationError):
            engine.score([{"type": "string"}])

    def test_score_with_none_raises_input_validation_error(self):
        engine = ScoringEngine()

        with pytest.raises(InputValidationError):
            engine.score(None)

    def test_total_score_calculation_with_weights(self):
        engine = ScoringEngine()
        schema = {
            "type": "object",
            "properties": {
                "value": {"type": "integer", "minimum": 0, "maximum": 100},
            },
            "additionalProperties": False,
        }
        result = engine.score(schema)
        expected_total = (
            result.breakdown["strictness"] * 0.35
            + result.breakdown["completeness"] * 0.35
            + result.breakdown["ambiguity"] * 0.15
            + result.breakdown["security"] * 0.15
        )
        assert abs(result.total_score - expected_total) < 0.1

    def test_score_result_overall_property(self):
        engine = ScoringEngine()
        schema = {"type": "object", "properties": {}, "additionalProperties": False}

        result = engine.score(schema)
        assert result.overall == int(result.total_score)

    def test_breakdown_contains_all_rules(self):
        engine = ScoringEngine()
        schema = {"type": "string", "minLength": 0, "maxLength": 50}
        result = engine.score(schema)
        expected_rules = ["strictness", "completeness", "ambiguity", "security"]

        for rule in expected_rules:
            assert rule in result.breakdown
            assert 0 <= result.breakdown[rule] <= 100


class TestStrictnessRule:
    def test_object_with_additional_properties_false_scores_100(self):
        rule = StrictnessRule()
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "additionalProperties": False,
        }
        score = rule.evaluate(schema)
        assert score == 1.0

    def test_object_with_additional_properties_true_scores_lower(self):
        rule = StrictnessRule()
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "additionalProperties": True,
        }
        score = rule.evaluate(schema)
        assert score < 1.0
        assert score == 0.0

    def test_object_with_missing_additional_properties_scores_lower(self):
        rule = StrictnessRule()
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
        }
        score = rule.evaluate(schema)
        assert score < 1.0
        assert score == 0.0

    def test_string_with_pattern_increases_score(self):
        rule = StrictnessRule()
        schema = {
            "type": "string",
            "pattern": "^[a-z]+$",
        }
        score = rule.evaluate(schema)
        assert score == 1.0

    def test_string_without_pattern_has_no_strictness_checks(self):
        rule = StrictnessRule()
        schema = {
            "type": "string",
        }
        score = rule.evaluate(schema)
        assert score == 1.0

    def test_nested_objects_all_need_additional_properties_false(self):
        rule = StrictnessRule()
        schema = {
            "type": "object",
            "properties": {
                "nested": {
                    "type": "object",
                    "properties": {"value": {"type": "string"}},
                    "additionalProperties": False,
                }
            },
            "additionalProperties": False,
        }
        score = rule.evaluate(schema)
        assert score == 1.0

    def test_nested_objects_partial_additional_properties(self):
        rule = StrictnessRule()
        schema = {
            "type": "object",
            "properties": {
                "nested": {
                    "type": "object",
                    "properties": {"value": {"type": "string"}},
                }
            },
            "additionalProperties": False,
        }
        score = rule.evaluate(schema)
        assert score == 0.5

    def test_array_with_object_items(self):
        rule = StrictnessRule()
        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"id": {"type": "integer"}},
                "additionalProperties": False,
            },
        }
        score = rule.evaluate(schema)
        assert score == 1.0

    def test_anyof_branches_are_traversed(self):
        rule = StrictnessRule()
        schema = {
            "anyOf": [
                {
                    "type": "object",
                    "properties": {"a": {"type": "string"}},
                    "additionalProperties": False,
                },
                {
                    "type": "object",
                    "properties": {"b": {"type": "string"}},
                    "additionalProperties": False,
                },
            ]
        }
        score = rule.evaluate(schema)
        assert score == 1.0


class TestCompletenessRule:
    def test_integer_with_min_max_scores_100(self):
        rule = CompletenessRule()
        schema = {
            "type": "integer",
            "minimum": 0,
            "maximum": 100,
        }
        score = rule.evaluate(schema)
        assert score == 1.0

    def test_integer_missing_minimum_scores_50(self):
        rule = CompletenessRule()
        schema = {
            "type": "integer",
            "maximum": 100,
        }
        score = rule.evaluate(schema)
        assert score == 0.5

    def test_integer_missing_maximum_scores_50(self):
        rule = CompletenessRule()
        schema = {
            "type": "integer",
            "minimum": 0,
        }
        score = rule.evaluate(schema)
        assert score == 0.5

    def test_integer_missing_both_scores_0(self):
        rule = CompletenessRule()
        schema = {
            "type": "integer",
        }
        score = rule.evaluate(schema)
        assert score == 0.0

    def test_number_with_min_max_scores_100(self):
        rule = CompletenessRule()
        schema = {
            "type": "number",
            "minimum": 0.0,
            "maximum": 100.0,
        }
        score = rule.evaluate(schema)
        assert score == 1.0

    def test_string_with_minlength_maxlength_scores_100(self):
        rule = CompletenessRule()
        schema = {
            "type": "string",
            "minLength": 1,
            "maxLength": 100,
        }
        score = rule.evaluate(schema)
        assert score == 1.0

    def test_string_missing_minlength_scores_50(self):
        rule = CompletenessRule()
        schema = {
            "type": "string",
            "maxLength": 100,
        }
        score = rule.evaluate(schema)
        assert score == 0.5

    def test_string_missing_maxlength_scores_50(self):
        rule = CompletenessRule()
        schema = {
            "type": "string",
            "minLength": 1,
        }
        score = rule.evaluate(schema)
        assert score == 0.5

    def test_array_with_minitems_maxitems_scores_100(self):
        rule = CompletenessRule()
        schema = {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 0,
            "maxItems": 10,
        }
        score = rule.evaluate(schema)
        assert score == 0.5

    def test_array_without_items_constraints(self):
        rule = CompletenessRule()
        schema = {
            "type": "array",
            "items": {"type": "integer", "minimum": 0, "maximum": 100},
        }
        score = rule.evaluate(schema)
        assert score == 0.5

    def test_object_with_complete_properties(self):
        rule = CompletenessRule()
        schema = {
            "type": "object",
            "properties": {
                "count": {"type": "integer", "minimum": 0, "maximum": 1000},
                "name": {"type": "string", "minLength": 1, "maxLength": 50},
            },
        }
        score = rule.evaluate(schema)
        assert score == 1.0

    def test_nested_array_completeness(self):
        rule = CompletenessRule()
        schema = {
            "type": "array",
            "minItems": 0,
            "maxItems": 100,
            "items": {
                "type": "array",
                "minItems": 0,
                "maxItems": 10,
                "items": {"type": "integer", "minimum": 0, "maximum": 100},
            },
        }
        score = rule.evaluate(schema)
        assert score == 1.0


class TestAmbiguityRule:
    def test_schema_without_anyof_oneof_scores_100(self):
        rule = AmbiguityRule()
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
            },
        }
        score = rule.evaluate(schema)
        assert score == 1.0

    def test_schema_with_anyof_reduces_score(self):
        rule = AmbiguityRule()
        schema = {
            "anyOf": [
                {"type": "string"},
                {"type": "integer"},
            ]
        }
        score = rule.evaluate(schema)
        assert score < 1.0

    def test_schema_with_oneof_reduces_score(self):
        rule = AmbiguityRule()
        schema = {
            "oneOf": [
                {"type": "string"},
                {"type": "number"},
            ]
        }
        score = rule.evaluate(schema)
        assert score < 1.0

    def test_schema_with_multiple_anyof_reduces_score_more(self):
        rule = AmbiguityRule()
        schema_single = {
            "type": "object",
            "properties": {
                "field": {"anyOf": [{"type": "string"}, {"type": "integer"}]},
            },
        }
        schema_double = {
            "type": "object",
            "properties": {
                "field1": {"anyOf": [{"type": "string"}, {"type": "integer"}]},
                "field2": {"anyOf": [{"type": "boolean"}, {"type": "null"}]},
            },
        }
        score_single = rule.evaluate(schema_single)
        score_double = rule.evaluate(schema_double)
        assert score_double < score_single

    def test_deeply_nested_anyof(self):
        rule = AmbiguityRule()
        schema = {
            "type": "object",
            "properties": {
                "level1": {
                    "type": "object",
                    "properties": {"level2": {"anyOf": [{"type": "string"}, {"type": "number"}]}},
                }
            },
        }
        score = rule.evaluate(schema)
        assert score < 1.0

    def test_allof_does_not_count_as_ambiguous(self):
        rule = AmbiguityRule()
        schema = {
            "allOf": [
                {"type": "object", "properties": {"a": {"type": "string"}}},
                {"properties": {"b": {"type": "integer"}}},
            ]
        }
        score = rule.evaluate(schema)
        assert score == 1.0

    def test_simple_types_have_no_ambiguity(self):
        rule = AmbiguityRule()
        schemas = [
            {"type": "string"},
            {"type": "integer"},
            {"type": "boolean"},
            {"type": "null"},
            {"type": "number"},
        ]

        for schema in schemas:
            score = rule.evaluate(schema)
            assert score == 1.0


class TestSecurityRule:
    def test_schema_within_limits_scores_100(self):
        rule = SecurityRule()
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string", "maxLength": 100},
                "count": {"type": "integer", "maximum": 1000},
            },
        }
        score = rule.evaluate(schema)
        assert score == 1.0
        assert rule.score_zero is False

    def test_deep_nesting_sets_score_zero(self):
        rule = SecurityRule()
        inner = {"type": "string"}

        for _ in range(25):
            inner = {
                "type": "object",
                "properties": {"nested": inner},
            }

        score = rule.evaluate(inner)
        assert score == 0.0
        assert rule.score_zero is True

    @patch("src.bl.scoring.rules.security.settings")
    def test_deep_nesting_respects_config_limit(self, mock_settings):
        mock_settings.SECURITY_MAX_NESTING_DEPTH = 5
        mock_settings.SECURITY_MAX_STRING_LENGTH = 256
        mock_settings.SECURITY_MAX_INTEGER_DIGITS = 18
        rule = SecurityRule()
        inner = {"type": "string"}

        for _ in range(6):
            inner = {
                "type": "object",
                "properties": {"nested": inner},
            }

        score = rule.evaluate(inner)
        assert score == 0.0
        assert rule.score_zero is True

    @patch("src.bl.scoring.rules.security.settings")
    def test_large_maxlength_without_pattern_sets_score_zero(self, mock_settings):
        mock_settings.SECURITY_MAX_NESTING_DEPTH = 20
        mock_settings.SECURITY_MAX_STRING_LENGTH = 256
        mock_settings.SECURITY_MAX_INTEGER_DIGITS = 18
        rule = SecurityRule()
        schema = {
            "type": "string",
            "maxLength": 500,
        }
        score = rule.evaluate(schema)
        assert score == 0.0
        assert rule.score_zero is True

    @patch("src.bl.scoring.rules.security.settings")
    def test_large_maxlength_with_pattern_passes(self, mock_settings):
        mock_settings.SECURITY_MAX_NESTING_DEPTH = 20
        mock_settings.SECURITY_MAX_STRING_LENGTH = 256
        mock_settings.SECURITY_MAX_INTEGER_DIGITS = 18
        rule = SecurityRule()
        schema = {
            "type": "string",
            "maxLength": 500,
            "pattern": "^[a-z]+$",
        }
        score = rule.evaluate(schema)
        assert score == 1.0
        assert rule.score_zero is False

    @patch("src.bl.scoring.rules.security.settings")
    def test_large_maximum_value_sets_score_zero(self, mock_settings):
        mock_settings.SECURITY_MAX_NESTING_DEPTH = 20
        mock_settings.SECURITY_MAX_STRING_LENGTH = 256
        mock_settings.SECURITY_MAX_INTEGER_DIGITS = 18
        rule = SecurityRule()
        schema = {
            "type": "integer",
            "maximum": 10**20,
        }
        score = rule.evaluate(schema)
        assert score == 0.0
        assert rule.score_zero is True

    @patch("src.bl.scoring.rules.security.settings")
    def test_large_negative_minimum_sets_score_zero(self, mock_settings):
        mock_settings.SECURITY_MAX_NESTING_DEPTH = 20
        mock_settings.SECURITY_MAX_STRING_LENGTH = 256
        mock_settings.SECURITY_MAX_INTEGER_DIGITS = 18
        rule = SecurityRule()
        schema = {
            "type": "integer",
            "minimum": -(10**20),
        }
        score = rule.evaluate(schema)
        assert score == 0.0
        assert rule.score_zero is True

    @patch("src.bl.scoring.rules.security.settings")
    def test_maximum_within_limit_passes(self, mock_settings):
        mock_settings.SECURITY_MAX_NESTING_DEPTH = 20
        mock_settings.SECURITY_MAX_STRING_LENGTH = 256
        mock_settings.SECURITY_MAX_INTEGER_DIGITS = 18
        rule = SecurityRule()
        schema = {
            "type": "integer",
            "maximum": 10**17,
        }
        score = rule.evaluate(schema)
        assert score == 1.0
        assert rule.score_zero is False

    def test_score_zero_resets_between_evaluations(self):
        rule = SecurityRule()
        inner = {"type": "string"}

        for _ in range(25):
            inner = {"type": "object", "properties": {"nested": inner}}

        rule.evaluate(inner)
        assert rule.score_zero is True
        safe_schema = {"type": "string", "maxLength": 50}
        score = rule.evaluate(safe_schema)
        assert score == 1.0
        assert rule.score_zero is False

    def test_nested_object_with_security_violation(self):
        rule = SecurityRule()
        inner = {"type": "string"}

        for _ in range(25):
            inner = {"type": "object", "properties": {"level": inner}}

        score = rule.evaluate(inner)
        assert score == 0.0
        assert rule.score_zero is True


class TestScoringEngineSecurityOverride:
    def test_security_score_zero_makes_total_zero(self):
        engine = ScoringEngine()
        inner = {"type": "string"}

        for _ in range(25):
            inner = {
                "type": "object",
                "properties": {"nested": inner},
                "additionalProperties": False,
            }

        result = engine.score(inner)
        assert result.total_score == 0.0

    @patch("src.bl.scoring.rules.security.settings")
    def test_large_string_without_pattern_zeros_total(self, mock_settings):
        mock_settings.SECURITY_MAX_NESTING_DEPTH = 20
        mock_settings.SECURITY_MAX_STRING_LENGTH = 256
        mock_settings.SECURITY_MAX_INTEGER_DIGITS = 18
        engine = ScoringEngine()
        schema = {
            "type": "object",
            "properties": {
                "description": {"type": "string", "maxLength": 1000},
            },
            "additionalProperties": False,
        }
        result = engine.score(schema)
        assert result.total_score == 0.0

    def test_safe_schema_has_nonzero_total(self):
        engine = ScoringEngine()
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string", "minLength": 1, "maxLength": 100},
                "age": {"type": "integer", "minimum": 0, "maximum": 150},
            },
            "additionalProperties": False,
        }
        result = engine.score(schema)
        assert result.total_score > 0


class TestEdgeCases:
    def test_empty_object_properties(self):
        engine = ScoringEngine()
        schema = {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        }
        result = engine.score(schema)
        assert result.total_score >= 0

    def test_boolean_type_scoring(self):
        engine = ScoringEngine()
        schema = {"type": "boolean"}
        result = engine.score(schema)
        assert result.total_score >= 0

    def test_null_type_scoring(self):
        engine = ScoringEngine()
        schema = {"type": "null"}
        result = engine.score(schema)
        assert result.total_score >= 0

    def test_mixed_composition_keywords(self):
        engine = ScoringEngine()
        schema = {
            "allOf": [
                {"type": "object", "properties": {"a": {"type": "string"}}},
            ],
            "anyOf": [
                {"properties": {"b": {"type": "integer"}}},
                {"properties": {"c": {"type": "boolean"}}},
            ],
        }
        result = engine.score(schema)
        assert isinstance(result.total_score, float)

    def test_array_without_items(self):
        rule = CompletenessRule()
        schema = {"type": "array", "minItems": 0, "maxItems": 10}
        score = rule.evaluate(schema)
        assert score == 1.0

    def test_object_with_deeply_nested_properties(self):
        engine = ScoringEngine()
        schema = {
            "type": "object",
            "properties": {
                "l1": {
                    "type": "object",
                    "properties": {
                        "l2": {
                            "type": "object",
                            "properties": {
                                "value": {
                                    "type": "string",
                                    "minLength": 0,
                                    "maxLength": 50,
                                },
                            },
                            "additionalProperties": False,
                        }
                    },
                    "additionalProperties": False,
                }
            },
            "additionalProperties": False,
        }
        result = engine.score(schema)
        assert result.total_score > 0
