from typing import Any


class SchemaBuilderError(Exception):
    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
        }


class ValidationError(SchemaBuilderError):
    def __init__(
        self,
        message: str,
        path: str | None = None,
        expected: Any | None = None,
        actual: Any | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.path = path
        self.expected = expected
        self.actual = actual
        super().__init__(message, details)

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()

        if self.path:
            result["path"] = self.path

        if self.expected is not None:
            result["expected"] = self.expected

        if self.actual is not None:
            result["actual"] = self.actual

        return result


class ConfigurationError(SchemaBuilderError):
    def __init__(
        self,
        message: str,
        config_file: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.config_file = config_file
        super().__init__(message, details)

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()

        if self.config_file:
            result["config_file"] = self.config_file

        return result


class AnalysisError(SchemaBuilderError):
    def __init__(
        self,
        message: str,
        operation: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.operation = operation
        super().__init__(message, details)

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()

        if self.operation:
            result["operation"] = self.operation

        return result


class SchemaInferenceError(SchemaBuilderError):
    def __init__(
        self,
        message: str,
        data_type: str | None = None,
        path: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.data_type = data_type
        self.path = path
        super().__init__(message, details)

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()

        if self.data_type:
            result["data_type"] = self.data_type

        if self.path:
            result["path"] = self.path

        return result


class ScoringError(SchemaBuilderError):
    def __init__(
        self,
        message: str,
        rule_name: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.rule_name = rule_name
        super().__init__(message, details)

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()

        if self.rule_name:
            result["rule_name"] = self.rule_name

        return result


class MockDataGenerationError(SchemaBuilderError):
    def __init__(
        self,
        message: str,
        validation_errors: list[str] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.validation_errors = validation_errors or []
        super().__init__(message, details)

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()

        if self.validation_errors:
            result["validation_errors"] = self.validation_errors

        return result


class InputValidationError(SchemaBuilderError):
    def __init__(
        self,
        message: str,
        field: str | None = None,
        expected_type: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.field = field
        self.expected_type = expected_type
        super().__init__(message, details)

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()

        if self.field:
            result["field"] = self.field

        if self.expected_type:
            result["expected_type"] = self.expected_type

        return result
