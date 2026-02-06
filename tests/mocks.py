from typing import List


class MockAIService:
    async def evaluate_schema(self, schema: List[str]) -> int | None:
        return 99
