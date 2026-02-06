import json
import re
from typing import Any, Optional

import openai

from src.core import get_logger
from src.core.config import settings

logger = get_logger(__name__)


class OpenAIService:
    def __init__(self):
        self.client = None

        if settings.ENABLE_AI:
            if settings.OPENAI_API_KEY:
                self.client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

                logger.info("OpenAI service initialized successfully")

            else:
                logger.warning("ENABLE_AI is True but OPENAI_API_KEY is missing")

        else:
            logger.info("AI features disabled via ENABLE_AI setting")

    async def evaluate_schema(self, schema: dict[str, Any]) -> Optional[int]:
        if not self.client:
            return None

        logger.debug("Evaluating schema quality with AI")
        schema_str = json.dumps(schema, indent=2)
        truncate_len = settings.AI_SCHEMA_TRUNCATE_LENGTH

        if len(schema_str) > truncate_len:
            schema_str = schema_str[:truncate_len] + "... (truncated)"
            logger.debug("Schema truncated for evaluation (original > %d chars)", truncate_len)

        prompt = (
            f"Evaluate the quality and security of the following JSON Schema.\n"
            f"Consider: Specificity (no empty objects), Security (max lengths, patterns), and Structure.\n"
            f"Schema: {schema_str}\n"
            f"Return ONLY a single integer score from 0 to 100."
        )

        try:
            res = await self._call_gpt(prompt)

            if res:
                match = re.search(r"\d+", res)

                if match:
                    score = int(match.group())
                    logger.debug("AI schema evaluation score: %d", score)

                    return score

            logger.warning("Could not parse AI evaluation response: %s", res)

            return None

        except (ValueError, json.JSONDecodeError, openai.OpenAIError) as e:
            # Catch expected errors during AI evaluation
            # Let programming errors propagate for debugging
            logger.error("Failed to evaluate schema: %s", e)

            return None

    async def _call_gpt(self, prompt: str) -> Optional[str]:
        try:
            response = await self.client.chat.completions.create(
                model=settings.AI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a schema helper."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=settings.AI_MAX_TOKENS,
                temperature=settings.AI_TEMPERATURE,
            )

            content = response.choices[0].message.content
            return content.strip() if content else None

        except openai.OpenAIError as e:
            # Catch OpenAI API errors (rate limits, auth, network issues, etc.)
            logger.error("GPT API call failed: %s", e)

            return None
