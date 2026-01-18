from typing import Any, Dict, List, Optional

from jsonschema import ValidationError as JsonSchemaValidationError

from src.shared.enums import SchemaKeyword
from src.bl.validator.config import ErrorMessageLoader


class FixSuggestionGenerator:
    """Generates fix suggestions for JSON Schema validation errors using YAML templates."""

    def __init__(self) -> None:
        self._message_loader = ErrorMessageLoader()

    def generate(
        self,
        error: JsonSchemaValidationError,
        path: str,
        expected_type: Optional[str],
        actual_type: str,
        constraint_name: Optional[str],
        constraint_value: Optional[Any],
        allowed_values: Optional[List[Any]],
    ) -> str:
        """Generate a fix suggestion for the given error."""
        validator = error.validator
        value = error.instance

        context = self._build_context(
            error=error,
            path=path,
            value=value,
            expected_type=expected_type,
            actual_type=actual_type,
            constraint_value=constraint_value,
            allowed_values=allowed_values,
            validator=validator,
        )

        template = self._message_loader.get_fix_template(validator)
        if template:
            return self._format_template(template, context)

        fallback = self._message_loader.get_fallback_fix()
        return self._format_template(fallback, context)

    def _build_context(
        self,
        error: JsonSchemaValidationError,
        path: str,
        value: Any,
        expected_type: Optional[str],
        actual_type: str,
        constraint_value: Optional[Any],
        allowed_values: Optional[List[Any]],
        validator: str,
    ) -> Dict[str, Any]:
        """Build context dictionary for template formatting."""
        context = {
            "path": path,
            "value": value,
            "value_repr": repr(value)[:50],
            "value_preview": str(value)[:50],
            "expected_type": expected_type or "",
            "actual_type": actual_type,
            "constraint_value": constraint_value,
            "constraint_value_repr": repr(constraint_value),
            "allowed_values": allowed_values,
            "validator": validator,
        }

        # Add validator-specific context
        self._add_length_context(context, value)
        self._add_required_context(context, error)
        self._add_property_context(context, path)

        return context

    def _add_length_context(self, context: Dict[str, Any], value: Any) -> None:
        """Add length-related context for minLength/maxLength/minItems/maxItems."""
        if isinstance(value, (str, list)):
            context["actual_length"] = len(value)
        else:
            context["actual_length"] = len(str(value)) if value else 0

    def _add_required_context(self, context: Dict[str, Any], error: JsonSchemaValidationError) -> None:
        """Add context for required validator errors."""
        missing_prop = self._message_loader.get_default("default_property")
        if "'" in error.message:
            parts = error.message.split("'")
            if len(parts) > 1:
                missing_prop = parts[1]
        context["missing_prop"] = missing_prop

    def _add_property_context(self, context: Dict[str, Any], path: str) -> None:
        """Add property name context for additionalProperties errors."""
        if path != "(root)":
            context["prop_name"] = path.split(".")[-1]
        else:
            context["prop_name"] = self._message_loader.get_default("unknown_property")

    def _format_template(self, template: str, context: Dict[str, Any]) -> str:
        """Format template with context, handling missing keys gracefully."""
        try:
            return template.format(**context)
        except KeyError as e:
            return f"Error formatting template: missing key {e}"
