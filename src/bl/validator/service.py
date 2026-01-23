from typing import Any, Dict, List

from jsonschema import Draft7Validator, SchemaError
from jsonschema.exceptions import _WrappedReferencingError

from src.core import get_logger
from src.shared.models import ValidationResult, ValidationError
from src.shared.exceptions import ValidationError as ValidationException
from .formatters import ErrorFormatter

logger = get_logger(__name__)


class SchemaValidator:

    def __init__(self):
        self.formatter = ErrorFormatter()
        logger.debug("SchemaValidator initialized")

    def validate_data_against_schema(
        self, schema: Dict[str, Any], data_list: List[Any]
    ) -> ValidationResult:
        logger.info("Validating %d objects against schema", len(data_list))

        try:
            validator = Draft7Validator(schema)
        except SchemaError as e:
            logger.error("Invalid schema provided: %s", e)
            raise ValidationException(
                message=f"Invalid schema: {e.message}",
                path=str(e.path) if e.path else None,
            ) from e

        all_errors: List[ValidationError] = []
        valid_count = 0

        for idx, item in enumerate(data_list):
            try:
                errors = list(validator.iter_errors(item))
            except _WrappedReferencingError as e:
                logger.error("Schema reference error during validation: %s", e)
                raise ValidationException(
                    message=f"Invalid schema reference: {str(e)}",
                    path=None,
                ) from e

            if errors:
                formatted_errors = self.formatter.format(idx, errors)
                all_errors.extend(formatted_errors)
                logger.debug("Object %d: %d validation errors", idx, len(errors))
            else:
                valid_count += 1

        is_valid = len(all_errors) == 0

        logger.info(
            "Validation complete: %d valid, %d total errors",
            valid_count,
            len(all_errors),
        )

        return ValidationResult(valid=is_valid, total_errors=len(all_errors), errors=all_errors)

    def validate_single(self, schema: Dict[str, Any], data: Any) -> ValidationResult:
        return self.validate_data_against_schema(schema, [data])
