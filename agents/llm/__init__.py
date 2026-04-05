"""LLMRouter — tries Ollama first, falls back to OpenAI GPT."""
import asyncio
import time

import httpx

from .ollama_client import OllamaClient
from .claude_fallback import ClaudeFallback

OLLAMA_TIMEOUT_THRESHOLD = 3.0
CIRCUIT_BREAK_SECONDS = 300  # Skip Ollama for 5 min after a failure


class LLMRouter:
    def __init__(self):
        self._ollama = OllamaClient()
        self._openai = ClaudeFallback()
        self._ollama_failed_at: float = 0.0

    async def generate(self, prompt: str, system: str | None = None) -> str:
        # Circuit breaker: skip Ollama if it failed recently
        if time.time() - self._ollama_failed_at > CIRCUIT_BREAK_SECONDS:
            try:
                return await asyncio.wait_for(
                    self._ollama.generate(prompt, system),
                    timeout=OLLAMA_TIMEOUT_THRESHOLD,
                )
            except Exception:
                self._ollama_failed_at = time.time()

        try:
            return await self._openai.generate(prompt, system)
        except Exception:
            return (
                "I'm here to support you. Our AI service is temporarily "
                "experiencing connectivity issues, but your message has been "
                "received. Please try again in a moment, or reach out to your "
                "counselor directly if you need immediate support."
            )


_router: LLMRouter | None = None


def get_llm_router() -> LLMRouter:
    global _router
    if _router is None:
        _router = LLMRouter()
    return _router
