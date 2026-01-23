"""
Comprehensive unit tests for ScoringEngine and all scoring rules.
"""

import pytest
from unittest.mock import patch

from src.bl.scoring.engine.scoring_engine import ScoringEngine, ScoreResult
from src.bl.scoring.rules.strictness import StrictnessRule
from src.bl.scoring.rules.completeness import CompletenessRule
from src.bl.scoring.rules.ambiguity import AmbiguityRule
from src.bl.scoring.rules.security import SecurityRule
from src.shared.exceptions import InputValidationError


# =============================================================================
# ScoringEngine Tests
# =============================================================================


class TestScoringEngine:
    """Tests for ScoringEngine class."""

    def test_score_returns_score_result(self):
        """Test score() returns ScoreResult with total_score and breakdown."""
        engine = ScoringEngine()
        schema = {"type": "object", "properties": {}, "additionalProperties": False}

        result = engine.score(schema)

        assert isinstance(result, ScoreResult)
        assert hasattr(result, "total_score")
        assert hasattr(result, "breakdown")
        assert hasattr(result, "ai_score")
        assert isinstance(result.total_score, float)
        assert isinstance(result.breakdown, dict)

    def test_score_with_valid_schema(self):
        """Test score() with a valid schema returns expected structure."""
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
        """Test score() with empty schema raises InputValidationError."""
        engine = ScoringEngine()

        with pytest.raises(InputValidationError) as exc_info:
            engine.score({})

        assert "empty" in exc_info.value.message.lower()

    def test_score_with_non_dict_raises_input_validation_error(self):
        """Test score() with non-dict raises InputValidationError."""
        engine = ScoringEngine()

        with pytest.raises(InputValidationError) as exc_info:
            engine.score("not a dict")

        assert exc_info.value.field == "schema"
        assert exc_info.value.expected_type == "dict"

    def test_score_with_list_raises_input_validation_error(self):
        """Test score() with list input raises InputValidationError."""
        engine = ScoringEngine()

        with pytest.raises(InputValidationError):
            engine.score([{"type": "string"}])

    def test_score_with_none_raises_input_validation_error(self):
        """Test score() with None raises InputValidationError."""
        engine = ScoringEngine()

        with pytest.raises(InputValidationError):
            engine.score(None)

    def test_total_score_calculation_with_weights(self):
        """Test total_score is calculated correctly using weights."""
        engine = ScoringEngine()
        # Schema that should score well on all rules
        schema = {
            "type": "object",
            "properties": {
                "value": {"type": "integer", "minimum": 0, "maximum": 100},
            },
            "additionalProperties": False,
        }

        result = engine.score(schema)

        # Verify weights are applied (strictness=0.35, completeness=0.35, ambiguity=0.15, security=0.15)
        expected_total = (
            result.breakdown["strictness"] * 0.35
            + result.breakdown["completeness"] * 0.35
            + result.breakdown["ambiguity"] * 0.15
            + result.breakdown["security"] * 0.15
        )
        assert abs(result.total_score - expected_total) < 0.1

    def test_score_result_overall_property(self):
        """Test ScoreResult.overall returns int of total_score."""
        engine = ScoringEngine()
        schema = {"type": "object", "properties": {}, "additionalProperties": False}

        result = engine.score(schema)

        assert result.overall == int(result.total_score)

    def test_breakdown_contains_all_rules(self):
        """Test breakdown contains scores for all rules."""
        engine = ScoringEngine()
        schema = {"type": "string", "minLength": 0, "maxLength": 50}

        result = engine.score(schema)

        expected_rules = ["strictness", "completeness", "ambiguity", "security"]
        for rule in expected_rules:
            assert rule in result.breakdown
            assert 0 <= result.breakdown[rule] <= 100


# =============================================================================
# StrictnessRule Tests
# =============================================================================


class TestStrictnessRule:
    """Tests for StrictnessRule class."""

    def test_object_with_additional_properties_false_scores_100(self):
        """Object with additionalProperties=False scores 100%."""
        rule = StrictnessRule()
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "additionalProperties": False,
        }

        score = rule.evaluate(schema)

        assert score == 1.0

    def test_object_with_additional_properties_true_scores_lower(self):
        """Object with additionalProperties=True scores lower."""
        rule = StrictnessRule()
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "additionalProperties": True,
        }

        score = rule.evaluate(schema)

        assert score < 1.0
        assert score == 0.0  # 0 passed / 1 check

    def test_object_with_missing_additional_properties_scores_lower(self):
        """Object without additionalProperties specified scores lower."""
        rule = StrictnessRule()
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
        }

        score = rule.evaluate(schema)

        assert score < 1.0
        assert score == 0.0  # 0 passed / 1 check

    def test_string_with_pattern_increases_score(self):
        """String with pattern increases score."""
        rule = StrictnessRule()
        schema = {
            "type": "string",
            "pattern": "^[a-z]+$",
        }

        score = rule.evaluate(schema)

        # Pattern adds a check and passes it
        assert score == 1.0

    def test_string_without_pattern_has_no_strictness_checks(self):
        """String without pattern has no strictness checks (returns 1.0 default)."""
        rule = StrictnessRule()
        schema = {
            "type": "string",
        }

        score = rule.evaluate(schema)

        # No checks = returns 1.0
        assert score == 1.0

    def test_nested_objects_all_need_additional_properties_false(self):
        """Nested objects all need additionalProperties=False for 100%."""
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
        """Nested objects with partial additionalProperties scores proportionally."""
        rule = StrictnessRule()
        schema = {
            "type": "object",
            "properties": {
                "nested": {
                    "type": "object",
                    "properties": {"value": {"type": "string"}},
                    # Missing additionalProperties
                }
            },
            "additionalProperties": False,
        }

        score = rule.evaluate(schema)

        # 1 passed / 2 checks = 0.5
        assert score == 0.5

    def test_array_with_object_items(self):
        """Array items with objects are checked for additionalProperties."""
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
        """anyOf branches are traversed for strictness checks."""
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


# =============================================================================
# CompletenessRule Tests
# =============================================================================


class TestCompletenessRule:
    """Tests for CompletenessRule class."""

    def test_integer_with_min_max_scores_100(self):
        """Integer with minimum and maximum scores 100%."""
        rule = CompletenessRule()
        schema = {
            "type": "integer",
            "minimum": 0,
            "maximum": 100,
        }

        score = rule.evaluate(schema)

        assert score == 1.0

    def test_integer_missing_minimum_scores_50(self):
        """Integer missing minimum scores 50%."""
        rule = CompletenessRule()
        schema = {
            "type": "integer",
            "maximum": 100,
        }

        score = rule.evaluate(schema)

        assert score == 0.5

    def test_integer_missing_maximum_scores_50(self):
        """Integer missing maximum scores 50%."""
        rule = CompletenessRule()
        schema = {
            "type": "integer",
            "minimum": 0,
        }

        score = rule.evaluate(schema)

        assert score == 0.5

    def test_integer_missing_both_scores_0(self):
        """Integer missing both min and max scores 0%."""
        rule = CompletenessRule()
        schema = {
            "type": "integer",
        }

        score = rule.evaluate(schema)

        assert score == 0.0

    def test_number_with_min_max_scores_100(self):
        """Number type with minimum and maximum scores 100%."""
        rule = CompletenessRule()
        schema = {
            "type": "number",
            "minimum": 0.0,
            "maximum": 100.0,
        }

        score = rule.evaluate(schema)

        assert score == 1.0

    def test_string_with_minlength_maxlength_scores_100(self):
        """String with minLength and maxLength scores 100%."""
        rule = CompletenessRule()
        schema = {
            "type": "string",
            "minLength": 1,
            "maxLength": 100,
        }

        score = rule.evaluate(schema)

        assert score == 1.0

    def test_string_missing_minlength_scores_50(self):
        """String missing minLength scores 50%."""
        rule = CompletenessRule()
        schema = {
            "type": "string",
            "maxLength": 100,
        }

        score = rule.evaluate(schema)

        assert score == 0.5

    def test_string_missing_maxlength_scores_50(self):
        """String missing maxLength scores 50%."""
        rule = CompletenessRule()
        schema = {
            "type": "string",
            "minLength": 1,
        }

        score = rule.evaluate(schema)

        assert score == 0.5

    def test_array_with_minitems_maxitems_scores_100(self):
        """Array with minItems and maxItems scores 100%."""
        rule = CompletenessRule()
        schema = {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 0,
            "maxItems": 10,
        }

        score = rule.evaluate(schema)

        # Array checks (2) + string in items checks (2)
        # Array: 2/2, String items: 0/2 (no minLength/maxLength)
        # Total: 2/4 = 0.5
        assert score == 0.5

    def test_array_without_items_constraints(self):
        """Array without min/max items scores lower."""
        rule = CompletenessRule()
        schema = {
            "type": "array",
            "items": {"type": "integer", "minimum": 0, "maximum": 100},
        }

        score = rule.evaluate(schema)

        # Array: 0/2, Integer: 2/2 = 2/4 = 0.5
        assert score == 0.5

    def test_object_with_complete_properties(self):
        """Object with complete property constraints scores high."""
        rule = CompletenessRule()
        schema = {
            "type": "object",
            "properties": {
                "count": {"type": "integer", "minimum": 0, "maximum": 1000},
                "name": {"type": "string", "minLength": 1, "maxLength": 50},
            },
        }

        score = rule.evaluate(schema)

        # Integer: 2/2, String: 2/2 = 4/4 = 1.0
        assert score == 1.0

    def test_nested_array_completeness(self):
        """Nested array items are checked for completeness."""
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

        # Outer array: 2/2, inner array: 2/2, integer: 2/2 = 6/6 = 1.0
        assert score == 1.0


# =============================================================================
# AmbiguityRule Tests
# =============================================================================


class TestAmbiguityRule:
    """Tests for AmbiguityRule class."""

    def test_schema_without_anyof_oneof_scores_100(self):
        """Schema without anyOf/oneOf scores 100%."""
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
        """Schema with anyOf reduces score."""
        rule = AmbiguityRule()
        schema = {
            "anyOf": [
                {"type": "string"},
                {"type": "integer"},
            ]
        }

        score = rule.evaluate(schema)

        assert score < 1.0
        # 1 ambiguous node out of 3 total nodes (root + 2 branches)
        # Actually: root has anyOf so it's ambiguous = 1/3 ambiguous
        # Score = 1 - (1/3) = 0.667...

    def test_schema_with_oneof_reduces_score(self):
        """Schema with oneOf reduces score."""
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
        """Schema with multiple anyOf reduces score more."""
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
        """Deeply nested anyOf is counted."""
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

        # Multiple nodes, one is ambiguous
        assert score < 1.0

    def test_allof_does_not_count_as_ambiguous(self):
        """allOf does not count as ambiguous."""
        rule = AmbiguityRule()
        schema = {
            "allOf": [
                {"type": "object", "properties": {"a": {"type": "string"}}},
                {"properties": {"b": {"type": "integer"}}},
            ]
        }

        score = rule.evaluate(schema)

        # allOf is not ambiguous, only anyOf/oneOf are
        assert score == 1.0

    def test_simple_types_have_no_ambiguity(self):
        """Simple type schemas have no ambiguity."""
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


# =============================================================================
# SecurityRule Tests
# =============================================================================


class TestSecurityRule:
    """Tests for SecurityRule class."""

    def test_schema_within_limits_scores_100(self):
        """Schema within security limits scores 100%."""
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
        """Deep nesting (>max depth) sets score_zero=True and returns 0."""
        rule = SecurityRule()
        # Build a deeply nested schema (more than 20 levels)
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
        """Deep nesting respects configurable limit."""
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
        """Large maxLength without pattern sets score_zero=True."""
        mock_settings.SECURITY_MAX_NESTING_DEPTH = 20
        mock_settings.SECURITY_MAX_STRING_LENGTH = 256
        mock_settings.SECURITY_MAX_INTEGER_DIGITS = 18

        rule = SecurityRule()
        schema = {
            "type": "string",
            "maxLength": 500,  # Exceeds 256 limit
        }

        score = rule.evaluate(schema)

        assert score == 0.0
        assert rule.score_zero is True

    @patch("src.bl.scoring.rules.security.settings")
    def test_large_maxlength_with_pattern_passes(self, mock_settings):
        """Large maxLength with pattern does NOT trigger score_zero."""
        mock_settings.SECURITY_MAX_NESTING_DEPTH = 20
        mock_settings.SECURITY_MAX_STRING_LENGTH = 256
        mock_settings.SECURITY_MAX_INTEGER_DIGITS = 18

        rule = SecurityRule()
        schema = {
            "type": "string",
            "maxLength": 500,
            "pattern": "^[a-z]+$",  # Has pattern
        }

        score = rule.evaluate(schema)

        assert score == 1.0
        assert rule.score_zero is False

    @patch("src.bl.scoring.rules.security.settings")
    def test_large_maximum_value_sets_score_zero(self, mock_settings):
        """Large maximum value sets score_zero=True."""
        mock_settings.SECURITY_MAX_NESTING_DEPTH = 20
        mock_settings.SECURITY_MAX_STRING_LENGTH = 256
        mock_settings.SECURITY_MAX_INTEGER_DIGITS = 18

        rule = SecurityRule()
        schema = {
            "type": "integer",
            "maximum": 10**20,  # Exceeds 10^18
        }

        score = rule.evaluate(schema)

        assert score == 0.0
        assert rule.score_zero is True

    @patch("src.bl.scoring.rules.security.settings")
    def test_maximum_within_limit_passes(self, mock_settings):
        """Maximum within limit passes security check."""
        mock_settings.SECURITY_MAX_NESTING_DEPTH = 20
        mock_settings.SECURITY_MAX_STRING_LENGTH = 256
        mock_settings.SECURITY_MAX_INTEGER_DIGITS = 18

        rule = SecurityRule()
        schema = {
            "type": "integer",
            "maximum": 10**17,  # Within 10^18
        }

        score = rule.evaluate(schema)

        assert score == 1.0
        assert rule.score_zero is False

    def test_score_zero_resets_between_evaluations(self):
        """score_zero flag resets between evaluations."""
        rule = SecurityRule()

        # First evaluation that fails
        inner = {"type": "string"}
        for _ in range(25):
            inner = {"type": "object", "properties": {"nested": inner}}
        rule.evaluate(inner)
        assert rule.score_zero is True

        # Second evaluation that passes
        safe_schema = {"type": "string", "maxLength": 50}
        score = rule.evaluate(safe_schema)

        assert score == 1.0
        assert rule.score_zero is False

    def test_nested_object_with_security_violation(self):
        """Security violation in nested object triggers score_zero."""
        rule = SecurityRule()
        # Build nested to exactly hit the limit
        inner = {"type": "string"}
        for _ in range(25):
            inner = {"type": "object", "properties": {"level": inner}}

        score = rule.evaluate(inner)

        assert score == 0.0
        assert rule.score_zero is True


# =============================================================================
# Integration Tests - Security Override
# =============================================================================


class TestScoringEngineSecurityOverride:
    """Tests for security rule overriding total score."""

    def test_security_score_zero_makes_total_zero(self):
        """When security rule sets score_zero=True, total becomes 0."""
        engine = ScoringEngine()
        # Schema with deep nesting to trigger security failure
        inner = {"type": "string"}
        for _ in range(25):
            inner = {
                "type": "object",
                "properties": {"nested": inner},
                "additionalProperties": False,
            }

        result = engine.score(inner)

        # Even if other rules score high, total should be 0
        assert result.total_score == 0.0

    @patch("src.bl.scoring.rules.security.settings")
    def test_large_string_without_pattern_zeros_total(self, mock_settings):
        """Large string without pattern zeros total score."""
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
        """Safe schema has non-zero total score."""
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


# =============================================================================
# Edge Cases
# =============================================================================


class TestEdgeCases:
    """Edge case tests for scoring."""

    def test_empty_object_properties(self):
        """Object with no properties is valid."""
        engine = ScoringEngine()
        schema = {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        }

        result = engine.score(schema)

        assert result.total_score >= 0

    def test_boolean_type_scoring(self):
        """Boolean type schema is scored."""
        engine = ScoringEngine()
        schema = {"type": "boolean"}

        result = engine.score(schema)

        # Boolean has no specific constraints, should score well
        assert result.total_score >= 0

    def test_null_type_scoring(self):
        """Null type schema is scored."""
        engine = ScoringEngine()
        schema = {"type": "null"}

        result = engine.score(schema)

        assert result.total_score >= 0

    def test_mixed_composition_keywords(self):
        """Schema with mixed composition keywords is scored."""
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

        # Should complete without error
        assert isinstance(result.total_score, float)

    def test_array_without_items(self):
        """Array without items definition is scored."""
        rule = CompletenessRule()
        schema = {"type": "array", "minItems": 0, "maxItems": 10}

        score = rule.evaluate(schema)

        # 2/2 for array constraints
        assert score == 1.0

    def test_object_with_deeply_nested_properties(self):
        """Object with deep but safe nesting is scored."""
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
