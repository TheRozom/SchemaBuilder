"""Regex generation without AI using frequency analysis and heuristics."""

import re
from typing import List, Optional, Set
from collections import Counter


class RegexGenerator:
    """Generates regex patterns from examples using frequency analysis."""

    # Pre-defined patterns for common data types
    COMMON_PATTERNS = {
        "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        "url": r"^https?://[^\s]+$",
        "phone_us": r"^\+?1?\s*\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})$",
        "phone_intl": r"^\+?[\d\s\-\(\)]+$",
        "zipcode_us": r"^\d{5}(-\d{4})?$",
        "date_iso": r"^\d{4}-\d{2}-\d{2}$",
        "date_us": r"^\d{1,2}/\d{1,2}/\d{2,4}$",
        "time": r"^\d{1,2}:\d{2}(:\d{2})?(\s?(AM|PM))?$",
        "ipv4": r"^(\d{1,3}\.){3}\d{1,3}$",
        "hex_color": r"^#[0-9a-fA-F]{6}$",
        "uuid": r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        "credit_card": r"^\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}$",
    }

    def __init__(self, use_common_patterns: bool = True):
        """
        Initialize regex generator.

        Args:
            use_common_patterns: Whether to try matching against common patterns first
        """
        self.use_common_patterns = use_common_patterns

    def generate(self, examples: List[str], strict: bool = True) -> Optional[str]:
        """
        Generate a regex pattern from example strings.

        Args:
            examples: List of example strings to learn from
            strict: If True, generate exact patterns; if False, allow more flexibility

        Returns:
            Generated regex pattern or None if unable to generate
        """
        if not examples:
            return None

        # Analyze basic character classes first (more specific)
        if all(ex.isdigit() for ex in examples):
            return self._generate_digit_pattern(examples, strict)

        if all(ex.isalpha() for ex in examples):
            return self._generate_alpha_pattern(examples, strict)

        if all(ex.isalnum() for ex in examples):
            return self._generate_alnum_pattern(examples, strict)

        # Try common patterns (for complex types like email, URL)
        if self.use_common_patterns:
            for pattern_name, pattern in self.COMMON_PATTERNS.items():
                if all(re.match(pattern, ex) for ex in examples):
                    return pattern

        # Check for uniform semantic characteristics
        if all(self._is_email(ex) for ex in examples):
            return self.COMMON_PATTERNS["email"]

        if all(self._is_url(ex) for ex in examples):
            return self.COMMON_PATTERNS["url"]

        if all(self._is_phone(ex) for ex in examples):
            return self.COMMON_PATTERNS["phone_intl"]

        if all(self._is_uuid(ex) for ex in examples):
            return self.COMMON_PATTERNS["uuid"]

        # Find common prefix/suffix
        common_prefix = self._find_common_prefix(examples)
        common_suffix = self._find_common_suffix(examples)

        if common_prefix or common_suffix:
            return self._generate_prefix_suffix_pattern(
                examples, common_prefix, common_suffix, strict
            )

        # Analyze character class distribution by position
        return self._generate_positional_pattern(examples, strict)

    def _generate_digit_pattern(self, examples: List[str], strict: bool) -> str:
        """Generate pattern for numeric strings."""
        min_len = min(len(ex) for ex in examples)
        max_len = max(len(ex) for ex in examples)

        if min_len == max_len:
            return rf"^\d{{{min_len}}}$"
        elif strict:
            return rf"^\d{{{min_len},{max_len}}}$"
        else:
            return r"^\d+$"

    def _generate_alpha_pattern(self, examples: List[str], strict: bool) -> str:
        """Generate pattern for alphabetic strings."""
        min_len = min(len(ex) for ex in examples)
        max_len = max(len(ex) for ex in examples)

        # Check case sensitivity
        all_lower = all(ex.islower() for ex in examples)
        all_upper = all(ex.isupper() for ex in examples)

        if all_lower:
            char_class = "[a-z]"
        elif all_upper:
            char_class = "[A-Z]"
        else:
            char_class = "[a-zA-Z]"

        if min_len == max_len:
            return rf"^{char_class}{{{min_len}}}$"
        elif strict:
            return rf"^{char_class}{{{min_len},{max_len}}}$"
        else:
            return rf"^{char_class}+$"

    def _generate_alnum_pattern(self, examples: List[str], strict: bool) -> str:
        """Generate pattern for alphanumeric strings."""
        min_len = min(len(ex) for ex in examples)
        max_len = max(len(ex) for ex in examples)

        if min_len == max_len:
            return rf"^[a-zA-Z0-9]{{{min_len}}}$"
        elif strict:
            return rf"^[a-zA-Z0-9]{{{min_len},{max_len}}}$"
        else:
            return r"^[a-zA-Z0-9]+$"

    def _generate_prefix_suffix_pattern(
        self, examples: List[str], prefix: str, suffix: str, strict: bool
    ) -> str:
        """Generate pattern with common prefix/suffix."""
        escaped_prefix = re.escape(prefix)
        escaped_suffix = re.escape(suffix)

        if prefix and suffix:
            middle_pattern = ".*" if not strict else ".+"
            return rf"^{escaped_prefix}{middle_pattern}{escaped_suffix}$"
        elif prefix:
            rest_pattern = ".*" if not strict else ".+"
            return rf"^{escaped_prefix}{rest_pattern}$"
        else:  # suffix only
            rest_pattern = ".*" if not strict else ".+"
            return rf"^{rest_pattern}{escaped_suffix}$"

    def _generate_positional_pattern(self, examples: List[str], strict: bool) -> Optional[str]:
        """Generate pattern based on character classes at each position."""
        if not examples:
            return None

        max_len = max(len(ex) for ex in examples)
        pattern_parts = []

        for i in range(max_len):
            chars_at_pos = [ex[i] for ex in examples if i < len(ex)]

            if not chars_at_pos:
                continue

            if all(c.isdigit() for c in chars_at_pos):
                pattern_parts.append(r"\d")
            elif all(c.isalpha() for c in chars_at_pos):
                # Check if all uppercase or all lowercase for stricter pattern
                if all(c.isupper() for c in chars_at_pos):
                    pattern_parts.append(r"[A-Z]")
                elif all(c.islower() for c in chars_at_pos):
                    pattern_parts.append(r"[a-z]")
                else:
                    pattern_parts.append(r"[a-zA-Z]")
            elif all(c.isspace() for c in chars_at_pos):
                pattern_parts.append(r"\s")
            elif all(c in "-_." for c in chars_at_pos):
                unique_chars = set(chars_at_pos)
                if len(unique_chars) == 1:
                    pattern_parts.append(re.escape(chars_at_pos[0]))
                else:
                    pattern_parts.append(f"[{re.escape(''.join(unique_chars))}]")
            else:
                # Mixed characters - create character class
                unique_chars = set(chars_at_pos)
                if len(unique_chars) == 1:
                    pattern_parts.append(re.escape(chars_at_pos[0]))
                else:
                    pattern_parts.append(f"[{re.escape(''.join(unique_chars))}]")

        return "^" + "".join(pattern_parts) + "$" if pattern_parts else None

    def _find_common_prefix(self, strings: List[str]) -> str:
        """Find the longest common prefix among strings."""
        if not strings:
            return ""

        prefix = strings[0]
        for s in strings[1:]:
            while not s.startswith(prefix):
                prefix = prefix[:-1]
                if not prefix:
                    return ""
        return prefix

    def _find_common_suffix(self, strings: List[str]) -> str:
        """Find the longest common suffix among strings."""
        if not strings:
            return ""

        suffix = strings[0]
        for s in strings[1:]:
            while not s.endswith(suffix):
                suffix = suffix[1:]
                if not suffix:
                    return ""
        return suffix

    def _is_email(self, s: str) -> bool:
        """Check if string looks like an email."""
        return "@" in s and "." in s.split("@")[-1]

    def _is_url(self, s: str) -> bool:
        """Check if string looks like a URL."""
        return s.startswith(("http://", "https://", "ftp://"))

    def _is_phone(self, s: str) -> bool:
        """Check if string looks like a phone number."""
        digits = re.sub(r"[^\d]", "", s)
        return len(digits) >= 7 and len(digits) <= 15

    def _is_uuid(self, s: str) -> bool:
        """Check if string looks like a UUID."""
        return bool(re.match(r"^[0-9a-f-]{36}$", s.lower()))

    def analyze_pattern(self, examples: List[str]) -> dict:
        """
        Analyze patterns in the examples without generating regex.

        Returns:
            Dictionary with pattern analysis
        """
        if not examples:
            return {}

        return {
            "count": len(examples),
            "min_length": min(len(ex) for ex in examples),
            "max_length": max(len(ex) for ex in examples),
            "all_digits": all(ex.isdigit() for ex in examples),
            "all_alpha": all(ex.isalpha() for ex in examples),
            "all_alnum": all(ex.isalnum() for ex in examples),
            "common_prefix": self._find_common_prefix(examples),
            "common_suffix": self._find_common_suffix(examples),
            "unique_count": len(set(examples)),
            "likely_type": self._infer_type(examples),
        }

    def _infer_type(self, examples: List[str]) -> Optional[str]:
        """Infer the likely data type from examples."""
        if all(self._is_email(ex) for ex in examples):
            return "email"
        if all(self._is_url(ex) for ex in examples):
            return "url"
        if all(self._is_phone(ex) for ex in examples):
            return "phone"
        if all(self._is_uuid(ex) for ex in examples):
            return "uuid"
        if all(ex.isdigit() for ex in examples):
            return "integer"
        if all(ex.isalpha() for ex in examples):
            return "text"
        return None
