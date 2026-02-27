from typing import Any

from jsonschema import Draft7Validator, SchemaError
from jsonschema.exceptions import _WrappedReferencingError

from src.core import get_logger
from src.core.service_config import service_config
from src.shared.exceptions import ValidationError as ValidationException
from src.shared.models import ValidationError, ValidationResult
from src.shared.utils import strip_required_keywords

logger = get_logger(__name__)


class SchemaValidator:
    def __init__(self):
        self.formatter = service_config.error_formatter
        logger.debug("SchemaValidator initialized")

    def validate_data_against_schema(
        self, schema: dict[str, Any], data_list: list[Any]
    ) -> ValidationResult:
        logger.info("Validating %d objects against schema", len(data_list))
        sanitized_schema = strip_required_keywords(schema)

        try:
            validator = Draft7Validator(sanitized_schema)

        except SchemaError as e:
            logger.error("Invalid schema provided: %s", e)
            raise ValidationException(
                message=f"Invalid schema: {e.message}",
                path=str(e.path) if e.path else None,
            ) from e

        all_errors: list[ValidationError] = []
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

    def validate_single(self, schema: dict[str, Any], data: Any) -> ValidationResult:
        return self.validate_data_against_schema(schema, [data])
