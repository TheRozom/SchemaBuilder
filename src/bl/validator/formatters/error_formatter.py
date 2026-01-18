from typing import List

from jsonschema import ValidationError as JsonSchemaValidationError

from src.shared.models import ValidationError
from src.bl.validator.extractors import ConstraintExtractor
from src.bl.validator.generators import FixSuggestionGenerator


class ErrorFormatter:
    """Formats JSON Schema validation errors with detailed fix information."""

    def __init__(self) -> None:
        self._extractor = ConstraintExtractor()
        self._generator = FixSuggestionGenerator()

    def format(self, idx: int, errors: List[JsonSchemaValidationError]) -> List[ValidationError]:
        """Format a list of validation errors for a single object."""
        formatted_errors = []
        for error in errors:
            formatted_errors.append(self._format_single_error(idx, error))
        return formatted_errors

    def _format_single_error(self, idx: int, error: JsonSchemaValidationError) -> ValidationError:
        """Format a single error with detailed fix information."""
        path = self._extractor.get_path(error)
        schema_path = self._extractor.get_schema_path(error)
        actual_type = self._extractor.get_actual_type(error)

        expected_type = self._extractor.get_expected_type(error)
        constraint_name = self._extractor.get_constraint_name(error)
        constraint_value = self._extractor.get_constraint_value(error)
        allowed_values = self._extractor.get_allowed_values(error)

        fix_suggestion = self._generator.generate(
            error=error,
            path=path,
            expected_type=expected_type,
            actual_type=actual_type,
            constraint_name=constraint_name,
            constraint_value=constraint_value,
            allowed_values=allowed_values,
        )

        return ValidationError(
            object_index=idx,
            path=path,
            message=error.message,
            validator=error.validator,
            failed_value=str(error.instance)[:100],
            schema_path=schema_path,
            expected_type=expected_type,
            actual_type=actual_type,
            constraint_name=constraint_name,
            constraint_value=constraint_value,
            allowed_values=allowed_values,
            fix_suggestion=fix_suggestion,
        )
