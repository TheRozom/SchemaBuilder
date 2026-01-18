from abc import ABC, abstractmethod
from typing import Any, Dict


class IRule(ABC):

    @abstractmethod
    def evaluate(self, schema: Dict[str, Any]) -> float:
        pass
