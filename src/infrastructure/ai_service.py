import json
import re
from typing import Any, Optional

import openai

from src.core import get_logger
from src.core.config import settings
from src.domain.interfaces import IAIService
from src.shared.exceptions import AIServiceError

logger = get_logger(__name__)


class OpenAIService(IAIService):

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

    async def generate_regex(self, samples: list[str]) -> Optional[str]:
        if not self.client or not samples:
            logger.debug("Skipping regex generation: client=%s, samples=%d",
                        self.client is not None, len(samples) if samples else 0)
            return None

        logger.debug("Generating regex for %d samples", len(samples))

        prompt = (
            f"Analyze these strings and generate a strict Python regular expression (regex) that matches them all.\n"
            f"Strings: {samples}\n"
            f"Return ONLY the regex string. Do not include quotes or backticks."
        )

        result = await self._call_gpt(prompt)
        if result:
            logger.debug("Generated regex: %s", result[:50])
        return result

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
                match = re.search(r'\d+', res)
                if match:
                    score = int(match.group())
                    logger.debug("AI schema evaluation score: %d", score)
                    return score
            logger.warning("Could not parse AI evaluation response: %s", res)
            return None
        except Exception as e:
            logger.error("Failed to evaluate schema: %s", e)
            return None

    async def _call_gpt(self, prompt: str) -> Optional[str]:
        try:
            response = await self.client.chat.completions.create(
                model=settings.AI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a schema helper."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=settings.AI_MAX_TOKENS,
                temperature=settings.AI_TEMPERATURE,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error("GPT API call failed: %s", e)
            return None
