"""Service layer for mock data generation and regex synthesis."""

from typing import Any, Dict, List, Optional, Tuple
from .semantic_detector import SemanticFieldDetector
from .regex_generator import RegexGenerator
from .mock_data_generator import MockDataGenerator


class GeneratorService:
    """High-level service for data generation and pattern synthesis."""

    def __init__(
        self,
        use_semantic_detection: bool = True,
        locale: str = "en_US",
        seed: Optional[int] = None,
    ):
        """
        Initialize generator service.

        Args:
            use_semantic_detection: Whether to use semantic field detection
            locale: Locale for data generation
            seed: Random seed for reproducibility
        """
        self.semantic_detector = SemanticFieldDetector() if use_semantic_detection else None
        self.regex_generator = RegexGenerator()
        self.mock_generator = MockDataGenerator(locale=locale, seed=seed)

    def generate_mock_data(
        self,
        schema: Dict[str, Any],
        count: int = 1,
        use_semantic_hints: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Generate mock data from a JSON schema with semantic understanding.

        Args:
            schema: JSON schema definition
            count: Number of records to generate
            use_semantic_hints: Whether to use semantic field detection

        Returns:
            List of generated mock data records
        """
        # Enhance schema with semantic field type detection
        if use_semantic_hints and self.semantic_detector:
            enhanced_schema = self._enhance_schema_with_semantics(schema)
        else:
            enhanced_schema = schema

        # Generate data
        result = self.mock_generator.generate_from_schema(enhanced_schema, count=count)

        # Return as list for consistency
        if isinstance(result, dict):
            return [result]
        return result

    def generate_from_examples(
        self, examples: List[Dict[str, Any]], count: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Generate mock data based on example records.

        Args:
            examples: List of example records
            count: Number of records to generate

        Returns:
            List of generated records
        """
        return self.mock_generator.generate_from_examples(examples, count=count)

    def infer_regex_pattern(self, examples: List[str], strict: bool = True) -> Optional[str]:
        """
        Infer regex pattern from example strings without using AI.

        Args:
            examples: List of example strings
            strict: Whether to generate strict or flexible patterns

        Returns:
            Generated regex pattern or None
        """
        return self.regex_generator.generate(examples, strict=strict)

    def analyze_field_pattern(self, examples: List[str]) -> Dict[str, Any]:
        """
        Analyze patterns in example strings.

        Args:
            examples: List of example strings

        Returns:
            Dictionary with pattern analysis
        """
        return self.regex_generator.analyze_pattern(examples)

    def detect_field_type(
        self, field_name: str, sample_values: Optional[List[str]] = None
    ) -> Tuple[Optional[str], float]:
        """
        Detect semantic field type.

        Args:
            field_name: Name of the field
            sample_values: Optional sample values

        Returns:
            Tuple of (detected_type, confidence)
        """
        if not self.semantic_detector:
            return None, 0.0

        return self.semantic_detector.detect_field_type(field_name, sample_values)

    def get_field_suggestions(self, field_name: str, top_k: int = 3) -> List[Tuple[str, float]]:
        """
        Get top K field type suggestions.

        Args:
            field_name: Name of the field
            top_k: Number of suggestions

        Returns:
            List of (field_type, confidence) tuples
        """
        if not self.semantic_detector:
            return []

        return self.semantic_detector.get_field_suggestions(field_name, top_k=top_k)

    def enhance_schema_with_patterns(
        self, schema: Dict[str, Any], examples_by_field: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """
        Enhance JSON schema with regex patterns from examples.

        Args:
            schema: JSON schema definition
            examples_by_field: Dictionary mapping field names to example values

        Returns:
            Enhanced schema with pattern properties
        """
        enhanced = schema.copy()
        properties = enhanced.get("properties", {})

        for field_name, examples in examples_by_field.items():
            if field_name in properties and examples:
                pattern = self.regex_generator.generate(examples, strict=False)
                if pattern:
                    properties[field_name]["pattern"] = pattern

        enhanced["properties"] = properties
        return enhanced

    def _enhance_schema_with_semantics(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance schema with semantic field type detection."""
        enhanced = schema.copy()
        properties = enhanced.get("properties", {})

        for field_name, field_schema in properties.items():
            # Skip if format is already specified
            if "format" in field_schema:
                continue

            # Detect field type
            detected_type, confidence = self.semantic_detector.detect_field_type(field_name)

            if detected_type and confidence > 0.7:
                # Map semantic type to JSON schema format
                format_mapping = {
                    "email": "email",
                    "url": "uri",
                    "date": "date",
                    "id": "uuid",
                }

                if detected_type in format_mapping:
                    field_schema["format"] = format_mapping[detected_type]
                    field_schema["x-semantic-type"] = detected_type
                elif detected_type in ["phone", "name", "address", "company", "job"]:
                    field_schema["x-semantic-type"] = detected_type

        enhanced["properties"] = properties
        return enhanced

    def generate_comprehensive_report(
        self, field_name: str, examples: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive report for a field.

        Args:
            field_name: Name of the field
            examples: Optional example values

        Returns:
            Comprehensive analysis report
        """
        report = {"field_name": field_name}

        # Semantic analysis
        if self.semantic_detector:
            detected_type, confidence = self.semantic_detector.detect_field_type(
                field_name, examples
            )
            suggestions = self.semantic_detector.get_field_suggestions(field_name)

            report["semantic"] = {
                "detected_type": detected_type,
                "confidence": confidence,
                "suggestions": suggestions,
            }

        # Pattern analysis
        if examples:
            pattern_analysis = self.regex_generator.analyze_pattern(examples)
            generated_pattern = self.regex_generator.generate(examples, strict=False)

            report["pattern"] = {
                "analysis": pattern_analysis,
                "generated_regex": generated_pattern,
            }

        return report
