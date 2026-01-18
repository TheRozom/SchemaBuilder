from typing import List
from src.domain.interfaces import IAIService

class MockAIService(IAIService):
    async def generate_regex(self, samples: List[str]) -> str | None:
        if "ABC" in samples[0]:
            return r"^ABC-\d+$"
        return None

    async def evaluate_schema(self, schema: List[str]) -> int | None:
        return 99
