from typing import Any, Dict, Protocol, runtime_checkable

from src.domain.models import SchemaDefinition


@runtime_checkable
class ISchemaService(Protocol):
    def generate_schema(self, data: Any) -> SchemaDefinition: ...


@runtime_checkable
class IAIService(Protocol):
    async def evaluate_schema(self, schema: Dict[str, Any]) -> int | None: ...
