from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class ValueGenerationStrategy(ABC):
    @abstractmethod
    def can_generate(self, field_name: str, field_schema: Dict[str, Any]) -> bool:
        pass

    @abstractmethod
    def generate(self, field_name: str, field_schema: Dict[str, Any]) -> Optional[Any]:
        pass
