"""OpenAI GPT fallback — activated when Ollama errors or exceeds timeout."""
import httpx

from src.config import settings

MODEL = "gpt-4o-mini"
TIMEOUT = 25.0
API_URL = "https://api.openai.com/v1/chat/completions"


class ClaudeFallback:
    def __init__(self):
        self._api_key = settings.ANTHROPIC_API_KEY  # Actually an OpenAI key

    async def generate(self, prompt: str, system: str | None = None) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": MODEL,
            "messages": messages,
            "max_tokens": 1024,
            "temperature": 0.7,
        }

        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(API_URL, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
