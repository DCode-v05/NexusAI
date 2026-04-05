"""SentenceTransformer all-MiniLM-L6-v2 wrapper — singleton loaded at startup."""
import asyncio
import numpy as np
from typing import ClassVar

MODEL_NAME = "all-MiniLM-L6-v2"


class ResourceEmbedder:
    _model: ClassVar = None

    @classmethod
    def _load(cls):
        if cls._model is None:
            from sentence_transformers import SentenceTransformer
            cls._model = SentenceTransformer(MODEL_NAME)

    def _embed_sync(self, texts: list[str]) -> np.ndarray:
        self._load()
        embeddings = self._model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return embeddings.astype(np.float32)

    async def embed(self, texts: list[str]) -> np.ndarray:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._embed_sync, texts)

    async def embed_single(self, text: str) -> np.ndarray:
        result = await self.embed([text])
        return result[0]
