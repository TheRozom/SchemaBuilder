import inspect
import json
from functools import wraps
from typing import Any, Dict, List

from fastapi import Request
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError as PydanticValidationError,
    field_validator,
    model_validator,
)

from src.shared import InputValidationError, ValidationException


class SchemaFieldMixin(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    json_schema: Dict[str, Any] = Field(..., alias="schema")

    @field_validator("json_schema")
    @classmethod
    def schema_must_not_be_empty(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        if not v:
            raise InputValidationError(message="Schema cannot be empty", field="schema")
        return v


class BuildSchemaRequest(BaseModel):
    data: List[Any]

    @model_validator(mode="after")
    def validate_data(self) -> "BuildSchemaRequest":
        if not self.data:
            raise InputValidationError(message="Data list cannot be empty", field="data")
        if not all(isinstance(item, dict) for item in self.data):
            raise InputValidationError(
                message="All items must be JSON objects (not arrays or primitives)",
                field="data",
                expected_type="object",
            )
        return self


class ScoreSchemaRequest(SchemaFieldMixin):
    pass


class AnalyzeRequest(BaseModel):
    data: List[Any]

    @model_validator(mode="after")
    def validate_data(self) -> "AnalyzeRequest":
        if not self.data:
            raise InputValidationError(message="Data list cannot be empty", field="data")
        return self


class ValidateRequest(SchemaFieldMixin):
    data: List[Any]

    @model_validator(mode="after")
    def validate_data(self) -> "ValidateRequest":
        if not self.data:
            raise InputValidationError(message="Data list cannot be empty", field="data")
        return self


class MockDataRequest(SchemaFieldMixin):
    count: int = Field(default=10, ge=1, le=1000)


def parse_body(model=None):
    def decorator(func):
        sig = inspect.signature(func)
        params = [p for p in sig.parameters.values() if p.name != "body"]

        request_param = inspect.Parameter(
            "request",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            annotation=Request,
        )
        params.insert(0, request_param)

        @wraps(func)
        async def wrapper(**kwargs):
            request_obj = kwargs.pop("request")
            body_bytes = await request_obj.body()
            body = None
            if body_bytes:
                try:
                    body = json.loads(body_bytes)
                except json.JSONDecodeError as e:
                    raise ValidationException(
                        message=f"Invalid JSON in request body: {e}",
                        details={"error": str(e)},
                    ) from e

            if model is not None:
                if body is None or not isinstance(body, dict):
                    raise InputValidationError(
                        message="Request body must be a JSON object",
                    )
                try:
                    body = model(**body)
                except PydanticValidationError as e:
                    raise InputValidationError(
                        message="Invalid request body",
                        details={"validation_errors": e.errors()},
                    ) from e

            kwargs["body"] = body
            result = func(**kwargs)
            if inspect.isawaitable(result):
                return await result
            return result

        wrapper.__signature__ = sig.replace(parameters=params)
        return wrapper

    return decorator
