from typing import Any, List, Optional

from jsonschema import ValidationError as JsonSchemaValidationError

from src.shared.enums import SchemaKeyword


class ConstraintExtractor:
    """Extracts constraint information from JSON Schema validation errors."""

    NUMERIC_VALIDATORS = [
        SchemaKeyword.MIN_LENGTH,
        SchemaKeyword.MAX_LENGTH,
        SchemaKeyword.MINIMUM,
        SchemaKeyword.MAXIMUM,
        SchemaKeyword.EXCLUSIVE_MINIMUM,
        SchemaKeyword.EXCLUSIVE_MAXIMUM,
        SchemaKeyword.MIN_ITEMS,
        SchemaKeyword.MAX_ITEMS,
        SchemaKeyword.MIN_PROPERTIES,
        SchemaKeyword.MAX_PROPERTIES,
        SchemaKeyword.MULTIPLE_OF,
    ]

    CONSTRAINT_VALIDATORS = [
        SchemaKeyword.MIN_LENGTH,
        SchemaKeyword.MAX_LENGTH,
        SchemaKeyword.MINIMUM,
        SchemaKeyword.MAXIMUM,
        SchemaKeyword.EXCLUSIVE_MINIMUM,
        SchemaKeyword.EXCLUSIVE_MAXIMUM,
        SchemaKeyword.PATTERN,
        SchemaKeyword.FORMAT,
        SchemaKeyword.ENUM,
        SchemaKeyword.CONST,
        SchemaKeyword.MULTIPLE_OF,
        SchemaKeyword.MIN_ITEMS,
        SchemaKeyword.MAX_ITEMS,
        SchemaKeyword.UNIQUE_ITEMS,
        SchemaKeyword.MIN_PROPERTIES,
        SchemaKeyword.MAX_PROPERTIES,
        SchemaKeyword.REQUIRED,
        SchemaKeyword.ADDITIONAL_PROPERTIES,
        SchemaKeyword.TYPE,
        SchemaKeyword.ANY_OF,
        SchemaKeyword.ONE_OF,
        SchemaKeyword.ALL_OF,
        SchemaKeyword.NOT,
    ]

    VALUE_VALIDATORS = [
        SchemaKeyword.PATTERN,
        SchemaKeyword.FORMAT,
        SchemaKeyword.CONST,
        SchemaKeyword.TYPE,
    ]

    def get_expected_type(self, error: JsonSchemaValidationError) -> Optional[str]:
        """Extract expected type from error schema."""
        schema = error.schema
        if isinstance(schema, dict):
            if SchemaKeyword.TYPE in schema:
                type_val = schema[SchemaKeyword.TYPE]
                return type_val if isinstance(type_val, str) else ", ".join(type_val)
            if SchemaKeyword.ANY_OF in schema:
                types = self._extract_types_from_any_of(schema[SchemaKeyword.ANY_OF])
                return (
                    f"{SchemaKeyword.ANY_OF}[{', '.join(types)}]"
                    if types
                    else SchemaKeyword.ANY_OF
                )
            if SchemaKeyword.ONE_OF in schema:
                return SchemaKeyword.ONE_OF
            if SchemaKeyword.ALL_OF in schema:
                return SchemaKeyword.ALL_OF
        if error.validator == SchemaKeyword.TYPE:
            return (
                error.validator_value
                if isinstance(error.validator_value, str)
                else ", ".join(error.validator_value)
            )
        return None

    def _extract_types_from_any_of(self, any_of_schema: List[Any]) -> List[str]:
        """Extract types from anyOf schema options."""
        types = []
        for option in any_of_schema:
            if isinstance(option, dict) and SchemaKeyword.TYPE in option:
                types.append(option[SchemaKeyword.TYPE])
        return types

    def get_constraint_name(self, error: JsonSchemaValidationError) -> Optional[str]:
        """Get the name of the constraint that failed."""
        if error.validator in self.CONSTRAINT_VALIDATORS:
            return error.validator
        return None

    def get_constraint_value(self, error: JsonSchemaValidationError) -> Optional[Any]:
        """Get the value of the constraint that failed."""
        if error.validator in self.NUMERIC_VALIDATORS:
            return error.validator_value
        if error.validator in self.VALUE_VALIDATORS:
            return error.validator_value
        return None

    def get_allowed_values(
        self, error: JsonSchemaValidationError
    ) -> Optional[List[Any]]:
        """Get allowed values if enum constraint failed."""
        if error.validator == SchemaKeyword.ENUM:
            return error.validator_value
        return None

    def get_path(self, error: JsonSchemaValidationError) -> str:
        """Get formatted path from error."""
        return ".".join(str(p) for p in error.path) if error.path else "(root)"

    def get_schema_path(self, error: JsonSchemaValidationError) -> str:
        """Get formatted schema path from error."""
        return (
            ".".join(str(p) for p in error.absolute_schema_path)
            if error.absolute_schema_path
            else ""
        )

    def get_actual_type(self, error: JsonSchemaValidationError) -> str:
        """Get actual type of the value."""
        return type(error.instance).__name__
