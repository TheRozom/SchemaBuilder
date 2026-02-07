from typing import Any, Protocol, runtime_checkable

from src.domain.models import SchemaDefinition


@runtime_checkable
class ISchemaService(Protocol):
    def generate_schema(self, data: Any) -> SchemaDefinition: ...
