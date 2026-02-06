from typing import Any, Protocol, runtime_checkable

from src.domain.models import SchemaDefinition


@runtime_checkable
class ISchemaService(Protocol):
    def generate_schema(self, data: Any) -> SchemaDefinition: ...


@runtime_checkable
class IAIService(Protocol):
    async def evaluate_schema(self, schema: dict[str, Any]) -> int | None: ...
