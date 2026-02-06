from abc import ABC, abstractmethod
from typing import Any


class ValueGenerationStrategy(ABC):
    @abstractmethod
    def can_generate(self, field_name: str, field_schema: dict[str, Any]) -> bool:
        pass

    @abstractmethod
    def generate(self, field_name: str, field_schema: dict[str, Any]) -> Any | None:
        pass
