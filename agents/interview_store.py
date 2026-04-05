"""In-memory mock interview session store — one session per UUID."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field


@dataclass
class InterviewTurn:
    role: str      # "interviewer" | "candidate"
    content: str


@dataclass
class InterviewSession:
    session_id: str
    role: str           # Target role being interviewed for
    question_num: int = 0        # Questions asked so far (0 = not started)
    total_questions: int = 5
    history: list[InterviewTurn] = field(default_factory=list)
    is_complete: bool = False

    def format_history(self) -> str:
        if not self.history:
            return ""
        lines = [f"{t.role.upper()}: {t.content}" for t in self.history]
        return "\n".join(lines)

    def append_interviewer(self, content: str) -> None:
        self.history.append(InterviewTurn(role="interviewer", content=content))

    def append_candidate(self, content: str) -> None:
        self.history.append(InterviewTurn(role="candidate", content=content))


class InterviewStore:
    def __init__(self):
        self._sessions: dict[str, InterviewSession] = {}

    def create(self, role: str) -> InterviewSession:
        session_id = str(uuid.uuid4())
        session = InterviewSession(session_id=session_id, role=role)
        self._sessions[session_id] = session
        return session

    def get(self, session_id: str) -> InterviewSession | None:
        return self._sessions.get(session_id)

    def delete(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)


_store = InterviewStore()


def get_interview_store() -> InterviewStore:
    return _store
