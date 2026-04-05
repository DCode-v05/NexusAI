"""In-memory conversation context store — last N turns per student_id.

Memory safety
─────────────
- Per-student deque is bounded by `max_turns` (default 10).
- The outer student dict is bounded by `max_students` (default 500).
- TTL-based eviction: students not accessed within `ttl_seconds` (default 2h)
  are removed by `evict_stale()`, which is called periodically from the
  lifespan background task in backend/src/main.py.
"""
from collections import deque
from dataclasses import dataclass, field
import time


@dataclass
class Turn:
    role: str       # "user" | "assistant"
    content: str
    risk_tier: str = "low"   # risk tier at the time of this turn


class ContextStore:
    def __init__(
        self,
        max_turns: int = 10,
        max_students: int = 500,
        ttl_seconds: int = 7200,   # 2 hours
    ):
        self._max_turns = max_turns
        self._max_students = max_students
        self._ttl = ttl_seconds
        self._store: dict[int, deque[Turn]] = {}
        self._last_access: dict[int, float] = {}   # student_id → epoch seconds

    def append(self, student_id: int, role: str, content: str, risk_tier: str = "low") -> None:
        now = time.monotonic()
        if student_id not in self._store:
            # Evict LRU student if at capacity before adding a new one
            if len(self._store) >= self._max_students:
                self._evict_lru()
            self._store[student_id] = deque(maxlen=self._max_turns)
        self._store[student_id].append(Turn(role=role, content=content, risk_tier=risk_tier))
        self._last_access[student_id] = now

    def get_history(self, student_id: int) -> list[Turn]:
        if student_id in self._store:
            self._last_access[student_id] = time.monotonic()
        return list(self._store.get(student_id, []))

    def format_history(self, student_id: int) -> str:
        turns = self.get_history(student_id)
        if not turns:
            return ""
        lines = [f"{t.role.upper()}: {t.content}" for t in turns]
        return "\n".join(lines)

    def get_last_risk_tier(self, student_id: int) -> str | None:
        """Return the risk tier of the most recent turn, or None if no history."""
        turns = self.get_history(student_id)
        if not turns:
            return None
        return turns[-1].risk_tier

    def clear(self, student_id: int) -> None:
        self._store.pop(student_id, None)
        self._last_access.pop(student_id, None)

    def evict_stale(self) -> int:
        """Remove students not accessed within TTL. Returns number of evictions."""
        cutoff = time.monotonic() - self._ttl
        stale = [sid for sid, t in self._last_access.items() if t < cutoff]
        for sid in stale:
            self._store.pop(sid, None)
            self._last_access.pop(sid, None)
        return len(stale)

    def _evict_lru(self) -> None:
        """Remove the least-recently-used student entry."""
        if not self._last_access:
            return
        lru_id = min(self._last_access, key=self._last_access.get)
        self.clear(lru_id)


_store = ContextStore()


def get_context_store() -> ContextStore:
    return _store
