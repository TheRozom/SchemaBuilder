"""Tests for RegexGenerator."""

import re
import pytest
from src.bl.generator.regex_generator import RegexGenerator


class TestRegexGenerator:
    """Test suite for RegexGenerator."""

    @pytest.fixture
    def generator(self):
        """Create a RegexGenerator instance."""
        return RegexGenerator()

    def test_digit_pattern_fixed_length(self, generator):
        """Test regex generation for fixed-length digit strings."""
        examples = ["1234", "5678", "9012"]
        pattern = generator.generate(examples, strict=True)

        assert pattern == r"^\d{4}$"
        for example in examples:
            assert re.match(pattern, example)

    def test_digit_pattern_variable_length(self, generator):
        """Test regex generation for variable-length digit strings."""
        examples = ["123", "5678", "90"]
        pattern = generator.generate(examples, strict=True)

        assert pattern == r"^\d{2,4}$"
        for example in examples:
            assert re.match(pattern, example)

    def test_alpha_pattern_lowercase(self, generator):
        """Test regex generation for lowercase alphabetic strings."""
        examples = ["hello", "world", "test"]
        pattern = generator.generate(examples, strict=True)

        assert pattern == r"^[a-z]{4,5}$"
        for example in examples:
            assert re.match(pattern, example)

    def test_alpha_pattern_uppercase(self, generator):
        """Test regex generation for uppercase alphabetic strings."""
        examples = ["HELLO", "WORLD"]
        pattern = generator.generate(examples, strict=True)

        assert pattern == r"^[A-Z]{5}$"
        for example in examples:
            assert re.match(pattern, example)

    def test_alnum_pattern(self, generator):
        """Test regex generation for alphanumeric strings."""
        examples = ["abc123", "def456", "ghi789"]
        pattern = generator.generate(examples, strict=True)

        assert pattern == r"^[a-zA-Z0-9]{6}$"
        for example in examples:
            assert re.match(pattern, example)

    def test_email_pattern(self, generator):
        """Test regex generation for email addresses."""
        examples = ["user@example.com", "admin@test.org", "info@company.net"]
        pattern = generator.generate(examples)

        assert pattern == generator.COMMON_PATTERNS["email"]
        for example in examples:
            assert re.match(pattern, example)

    def test_url_pattern(self, generator):
        """Test regex generation for URLs."""
        examples = [
            "https://example.com",
            "http://test.org",
            "https://company.net/path",
        ]
        pattern = generator.generate(examples)

        assert pattern == generator.COMMON_PATTERNS["url"]
        for example in examples:
            assert re.match(pattern, example)

    def test_phone_pattern(self, generator):
        """Test regex generation for phone numbers."""
        examples = ["+1 234-567-8900", "+44 20 1234 5678", "+33 1 23 45 67 89"]
        pattern = generator.generate(examples)

        assert pattern == generator.COMMON_PATTERNS["phone_intl"]
        for example in examples:
            assert re.match(pattern, example)

    def test_uuid_pattern(self, generator):
        """Test regex generation for UUIDs."""
        examples = [
            "550e8400-e29b-41d4-a716-446655440000",
            "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
            "6ba7b811-9dad-11d1-80b4-00c04fd430c8",
        ]
        pattern = generator.generate(examples)

        assert pattern == generator.COMMON_PATTERNS["uuid"]
        for example in examples:
            assert re.match(pattern, example)

    def test_common_prefix_pattern(self, generator):
        """Test regex generation with common prefix."""
        examples = ["user_john", "user_jane", "user_bob"]
        pattern = generator.generate(examples, strict=False)

        assert pattern.startswith("^user_")
        for example in examples:
            assert re.match(pattern, example)

    def test_common_suffix_pattern(self, generator):
        """Test regex generation with common suffix."""
        examples = ["john_email", "jane_email", "bob_email"]
        pattern = generator.generate(examples, strict=False)

        assert pattern.endswith("_email$")
        for example in examples:
            assert re.match(pattern, example)

    def test_positional_pattern(self, generator):
        """Test regex generation based on character positions."""
        examples = ["A-1", "B-2", "C-3"]
        pattern = generator.generate(examples, strict=True)

        # Should match uppercase letter, dash, digit
        assert re.match(pattern, "D-4")
        assert re.match(pattern, "Z-9")
        assert not re.match(pattern, "A1")  # Missing dash
        assert not re.match(pattern, "a-1")  # Lowercase

    def test_empty_examples(self, generator):
        """Test with empty examples list."""
        pattern = generator.generate([])
        assert pattern is None

    def test_analyze_pattern(self, generator):
        """Test pattern analysis without generating regex."""
        examples = ["123", "456", "789"]
        analysis = generator.analyze_pattern(examples)

        assert analysis["count"] == 3
        assert analysis["min_length"] == 3
        assert analysis["max_length"] == 3
        assert analysis["all_digits"] is True
        assert analysis["all_alpha"] is False
        assert analysis["unique_count"] == 3
        assert analysis["likely_type"] == "integer"

    def test_analyze_email_type(self, generator):
        """Test type inference for email addresses."""
        examples = ["user@test.com", "admin@example.org"]
        analysis = generator.analyze_pattern(examples)

        assert analysis["likely_type"] == "email"

    def test_analyze_url_type(self, generator):
        """Test type inference for URLs."""
        examples = ["https://example.com", "http://test.org"]
        analysis = generator.analyze_pattern(examples)

        assert analysis["likely_type"] == "url"

    def test_strict_vs_flexible(self, generator):
        """Test difference between strict and flexible pattern generation."""
        examples = ["12", "345", "6789"]

        strict_pattern = generator.generate(examples, strict=True)
        flexible_pattern = generator.generate(examples, strict=False)

        # Strict should have length constraints
        assert "{" in strict_pattern or "," in strict_pattern

        # Flexible should be simpler
        assert flexible_pattern == r"^\d+$"

    def test_common_patterns_disabled(self):
        """Test with common patterns disabled."""
        generator = RegexGenerator(use_common_patterns=False)
        examples = ["user@test.com", "admin@example.org"]

        # Should still detect email but might return different pattern
        pattern = generator.generate(examples)
        assert pattern is not None

    def test_mixed_case_alpha(self, generator):
        """Test mixed case alphabetic strings."""
        examples = ["Hello", "World", "Test"]
        pattern = generator.generate(examples, strict=True)

        assert "[a-zA-Z]" in pattern or "[A-Z]" in pattern.lower()
        for example in examples:
            assert re.match(pattern, example)

    def test_find_common_prefix(self, generator):
        """Test common prefix detection."""
        strings = ["prefix_one", "prefix_two", "prefix_three"]
        prefix = generator._find_common_prefix(strings)
        assert prefix == "prefix_"

    def test_find_common_suffix(self, generator):
        """Test common suffix detection."""
        strings = ["one_suffix", "two_suffix", "three_suffix"]
        suffix = generator._find_common_suffix(strings)
        assert suffix == "_suffix"

    def test_is_email(self, generator):
        """Test email detection."""
        assert generator._is_email("user@example.com") is True
        assert generator._is_email("notanemail") is False
        assert generator._is_email("@missing.com") is True  # Technically has @
        assert generator._is_email("user@") is False

    def test_is_url(self, generator):
        """Test URL detection."""
        assert generator._is_url("https://example.com") is True
        assert generator._is_url("http://test.org") is True
        assert generator._is_url("ftp://files.net") is True
        assert generator._is_url("notaurl") is False

    def test_is_phone(self, generator):
        """Test phone number detection."""
        assert generator._is_phone("123-456-7890") is True
        assert generator._is_phone("+1 (234) 567-8900") is True
        assert generator._is_phone("123") is False  # Too short
        assert generator._is_phone("12345678901234567890") is False  # Too long

    def test_is_uuid(self, generator):
        """Test UUID detection."""
        assert generator._is_uuid("550e8400-e29b-41d4-a716-446655440000") is True
        assert generator._is_uuid("550E8400-E29B-41D4-A716-446655440000") is True
        assert generator._is_uuid("not-a-uuid") is False
        assert generator._is_uuid("550e8400-e29b-41d4") is False  # Too short
