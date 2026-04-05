"""Whisper small — async audio-to-text transcription."""
import asyncio
import tempfile
import os
from typing import ClassVar


class Transcriber:
    _model: ClassVar = None

    @classmethod
    def _load(cls):
        if cls._model is None:
            import whisper
            cls._model = whisper.load_model("small")

    def _transcribe_sync(self, audio_bytes: bytes) -> str:
        self._load()
        import whisper
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        try:
            result = self._model.transcribe(tmp_path)
            return result.get("text", "").strip()
        finally:
            os.unlink(tmp_path)

    async def transcribe(self, audio_bytes: bytes) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._transcribe_sync, audio_bytes)
