from abc import ABC, abstractmethod
from typing import Any, Dict, List
from src.domain.models import SchemaDefinition


class ISchemaService(ABC):

    @abstractmethod
    async def generate_schema(self, data: Any) -> SchemaDefinition:
        pass


class IAIService(ABC):

    @abstractmethod
    async def generate_regex(self, samples: List[str]) -> str | None:
        pass

    @abstractmethod
    async def evaluate_schema(self, schema: Dict[str, Any]) -> int | None:
        pass
