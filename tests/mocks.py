class MockAIService:
    async def evaluate_schema(self, schema: list[str]) -> int | None:
        return 99
