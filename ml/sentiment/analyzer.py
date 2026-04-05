"""distilbert-base-uncased-finetuned-sst-2 sentiment analyzer.

Returns a distress_score in [0, 1] where 1 = maximum negative sentiment.
Loaded once at process start (singleton) to avoid repeated model loading.
"""
import asyncio
from typing import ClassVar

from ml.sentiment.preprocessor import clean_text

_DISTILBERT_MODEL = "distilbert-base-uncased-finetuned-sst-2-english"


class SentimentAnalyzer:
    _pipeline: ClassVar = None

    @classmethod
    def _load(cls):
        if cls._pipeline is None:
            from transformers import pipeline as hf_pipeline
            cls._pipeline = hf_pipeline(
                "sentiment-analysis",
                model=_DISTILBERT_MODEL,
                truncation=True,
                max_length=512,
            )

    def _analyze_sync(self, text: str) -> float:
        self._load()
        result = self._pipeline(text[:512])[0]
        label = result["label"]   # "POSITIVE" or "NEGATIVE"
        score = result["score"]   # confidence in [0, 1]
        # Map NEGATIVE confidence to distress score
        if label == "NEGATIVE":
            return float(score)
        else:
            return float(1.0 - score)

    async def analyze(self, text: str) -> float:
        cleaned = clean_text(text)
        if not cleaned:
            return 0.0
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._analyze_sync, cleaned)
