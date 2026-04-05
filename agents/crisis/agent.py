"""CrisisAgent — multi-signal gate → counselor alert + iCall helpline."""
from __future__ import annotations

import asyncio
import logging

import httpx

from agents.llm import get_llm_router
from src.config import settings

logger = logging.getLogger(__name__)

MCP_COUNSELOR_URL = settings.MCP_COUNSELOR_ALERTS_URL
ICALL_HELPLINE = "9152987821"

CRISIS_SYSTEM = (
    "You are NexusAI's crisis support companion. A student may be in severe distress. "
    "Your response must:\n"
    "1. Acknowledge their pain with deep compassion — they are heard and not alone.\n"
    "2. Clearly provide the iCall helpline: 9152987821 (available Mon–Sat, 8am–10pm).\n"
    "3. Let them know a counselor has been notified and will reach out.\n"
    "4. Encourage them to reach out to a trusted person immediately.\n"
    "Keep the response warm, human, and brief. Do NOT include any PII."
)

# Signal thresholds
ANOMALY_THRESHOLD = 0.7
SENTIMENT_THRESHOLD = 0.75
SURVEY_CRISIS_THRESHOLD = 2.0

# Retry config for counselor alert creation
_ALERT_RETRIES = 3
_ALERT_RETRY_DELAY = 1.0   # seconds between attempts


def is_crisis(
    anomaly_score: float,
    sentiment_score: float,
    survey_score: float | None,
    triggered_keywords: list[str] | None = None,
    risk_score: float = 0.0,
) -> bool:
    """Multi-tier crisis gate — loosened from strict AND to OR across tiers.

    Tier 1 — Explicit keyword + at least one corroborating signal:
        A crisis keyword alone (without any corroboration) avoids false positives
        from passing mentions, but any additional signal confirms intent.

    Tier 2 — High composite risk score alone:
        If the fused risk score already hit crisis threshold (≥0.8) this is enough.

    Tier 3 — Two-signal convergence (relaxed from original three-signal AND):
        Any two of [anomaly, sentiment, survey] above threshold is sufficient.
    """
    keyword_hit = bool(triggered_keywords)
    survey_hit = survey_score is not None and survey_score <= SURVEY_CRISIS_THRESHOLD

    # Tier 1: keyword + one corroborating signal
    if keyword_hit and (sentiment_score >= 0.5 or anomaly_score >= 0.5 or risk_score >= 0.6):
        return True

    # Tier 2: high fused risk score
    if risk_score >= 0.8:
        return True

    # Tier 3: two-signal convergence (any pair)
    two_signal = (
        (anomaly_score >= ANOMALY_THRESHOLD and sentiment_score >= SENTIMENT_THRESHOLD)
        or (anomaly_score >= ANOMALY_THRESHOLD and survey_hit)
        or (sentiment_score >= SENTIMENT_THRESHOLD and survey_hit)
    )
    return two_signal


class CrisisAgent:
    def __init__(self):
        self._llm = get_llm_router()

    async def handle(
        self,
        student_id: int,
        message: str,
        anomaly_score: float,
        sentiment_score: float,
        survey_score: float | None = None,
        triggered_keywords: list[str] | None = None,
        risk_score: float = 0.0,
        history: str = "",
    ) -> dict:
        alert_id, alert_created = await self._create_counselor_alert_with_retry(
            student_id=student_id,
            anomaly_score=anomaly_score,
            sentiment_score=sentiment_score,
            survey_score=survey_score or 0.0,
            triggered_keywords=triggered_keywords or [],
            risk_score=risk_score,
        )

        prompt = message
        if history:
            prompt = f"Conversation history:\n{history}\n\nStudent: {message}"

        # If the alert could not be created, note it in the system prompt so the
        # LLM still urges the student to contact support directly.
        system = CRISIS_SYSTEM
        if not alert_created:
            system += (
                "\n\nIMPORTANT: Counselor notification is currently unavailable. "
                "Strongly urge the student to call the helpline or walk to campus support NOW."
            )

        llm_response = await self._llm.generate(prompt, system)

        return {
            "response": llm_response,
            "helpline": ICALL_HELPLINE,
            "counselor_notified": alert_created,
            "alert_id": alert_id,
        }

    async def _create_counselor_alert_with_retry(
        self,
        student_id: int,
        anomaly_score: float,
        sentiment_score: float,
        survey_score: float,
        triggered_keywords: list[str],
        risk_score: float,
    ) -> tuple[int | None, bool]:
        """Attempt to create a counselor alert, retrying up to _ALERT_RETRIES times.

        Returns (alert_id, success_flag).
        """
        payload = {
            "student_id": student_id,
            "risk_score": risk_score or (
                0.5 * anomaly_score + 0.35 * sentiment_score
                + 0.15 * min(survey_score / 10.0, 1.0)
            ),
            "anomaly_score": anomaly_score,
            "sentiment_score": sentiment_score,
            "survey_score": survey_score,
            "triggered_keywords": triggered_keywords,
        }

        last_exc: Exception | None = None
        for attempt in range(1, _ALERT_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    r = await client.post(
                        f"{MCP_COUNSELOR_URL}/tools/create_alert",
                        json=payload,
                    )
                    r.raise_for_status()
                    alert_id = r.json().get("alert_id")
                    logger.info(
                        "Counselor alert created: student=%s alert_id=%s", student_id, alert_id
                    )
                    return alert_id, True
            except Exception as exc:
                last_exc = exc
                logger.warning(
                    "Counselor alert attempt %d/%d failed for student %s: %s",
                    attempt, _ALERT_RETRIES, student_id, exc,
                )
                if attempt < _ALERT_RETRIES:
                    await asyncio.sleep(_ALERT_RETRY_DELAY)

        # All retries exhausted — log at ERROR level so monitoring catches it
        logger.error(
            "CRITICAL: Failed to create counselor alert for student %s after %d attempts. "
            "Last error: %s. Manual intervention may be required.",
            student_id, _ALERT_RETRIES, last_exc,
        )
        return None, False


_agent: CrisisAgent | None = None


def get_crisis_agent() -> CrisisAgent:
    global _agent
    if _agent is None:
        _agent = CrisisAgent()
    return _agent
