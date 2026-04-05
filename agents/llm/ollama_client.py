"""Async client for the remote Ollama server at http://10.1.76.234:11434.

Model: gpt-oss (configured via OLLAMA_MODEL env var)
Request format: {"model": "gpt-oss", "prompt": "...", "stream": false}
"""
import httpx
from src.config import settings

TIMEOUT = 3.0
MAX_RETRIES = 1


class OllamaClient:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL

    async def generate(self, prompt: str, system: str | None = None) -> str:
        full_prompt = f"{system}\n\n{prompt}" if system else prompt

        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
        }

        for attempt in range(MAX_RETRIES):
            try:
                async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                    response = await client.post(
                        f"{self.base_url}/api/generate",
                        json=payload,
                    )
                    response.raise_for_status()
                    data = response.json()
                    return data.get("response", "").strip()
            except (httpx.TimeoutException, httpx.HTTPStatusError) as e:
                if attempt == MAX_RETRIES - 1:
                    raise
                continue

        raise RuntimeError("Ollama request failed after retries")
