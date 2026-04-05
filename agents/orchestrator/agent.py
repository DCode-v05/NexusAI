"""OrchestratorAgent — routes signals to specialist agents."""
from __future__ import annotations

import logging

import httpx

from ml.anomaly.detector import AnomalyDetector
from ml.sentiment.analyzer import SentimentAnalyzer
from ml.risk.scorer import RiskScorer, RiskResult

from agents.orchestrator.context_store import get_context_store
from agents.orchestrator.router_logic import route
from agents.wellbeing.agent import get_wellbeing_agent
from agents.pathway.agent import get_pathway_agent
from agents.crisis.agent import get_crisis_agent, is_crisis

from src.config import settings

logger = logging.getLogger(__name__)

MCP_STUDENT_URL = settings.MCP_STUDENT_DB_URL

_anomaly = AnomalyDetector()
_sentiment = SentimentAnalyzer()
_scorer = RiskScorer()

# Tier ordering for escalation comparison
_TIER_RANK = {"low": 0, "moderate": 1, "high": 2, "crisis": 3}


class OrchestratorAgent:
    def __init__(self):
        self._ctx = get_context_store()
        self._wellbeing = get_wellbeing_agent()
        self._pathway = get_pathway_agent()
        self._crisis = get_crisis_agent()

    async def process(
        self,
        student_id: int,
        message: str,
        survey_score: float | None = None,
    ) -> dict:
        behavior = await self._fetch_behavior(student_id)
        anomaly_score = await _anomaly.predict_from_log(behavior) if behavior else 0.0
        sentiment_score = await _sentiment.analyze(message)

        survey_decline = 0.0
        if survey_score is not None:
            survey_decline = max(0.0, 1.0 - survey_score / 10.0)

        risk: RiskResult = _scorer.compute(anomaly_score, sentiment_score, survey_decline)

        history = self._ctx.format_history(student_id)
        prev_tier = self._ctx.get_last_risk_tier(student_id)

        # Route based on current risk score and message content
        agent_name, triggered_keywords = route(risk.score, message)

        # Mid-conversation escalation check:
        # If the student was previously at low/moderate risk but current turn
        # has jumped to high or crisis, force escalation to the crisis agent.
        if prev_tier is not None:
            prev_rank = _TIER_RANK.get(prev_tier, 0)
            curr_rank = _TIER_RANK.get(risk.tier, 0)
            escalated = curr_rank - prev_rank >= 2   # jumped 2+ tiers (e.g. low→high)
            if escalated and risk.tier in ("high", "crisis"):
                logger.warning(
                    "Risk escalation detected for student %s: %s → %s. Overriding to crisis agent.",
                    student_id, prev_tier, risk.tier,
                )
                agent_name = "crisis"

        # Also run the secondary is_crisis gate for cases the router may have missed
        if agent_name != "crisis" and is_crisis(
            anomaly_score,
            sentiment_score,
            survey_score,
            triggered_keywords=triggered_keywords,
            risk_score=risk.score,
        ):
            logger.info(
                "is_crisis() gate triggered for student %s (router said '%s'). Escalating.",
                student_id, agent_name,
            )
            agent_name = "crisis"

        # Dispatch to specialist agent
        if agent_name == "crisis":
            result = await self._crisis.handle(
                student_id=student_id,
                message=message,
                anomaly_score=anomaly_score,
                sentiment_score=sentiment_score,
                survey_score=survey_score,
                triggered_keywords=triggered_keywords,
                risk_score=risk.score,
                history=history,
            )
            response_text = result["response"]
        elif agent_name == "pathway":
            response_text = await self._pathway.chat(
                message=message,
                history=history,
            )
            result = {}
        else:
            response_text = await self._wellbeing.respond(
                message=message,
                risk_tier=risk.tier,
                history=history,
            )
            result = {}

        # Store turn with risk tier so next call can detect escalation
        self._ctx.append(student_id, "user", message, risk_tier=risk.tier)
        self._ctx.append(student_id, "assistant", response_text, risk_tier=risk.tier)

        return {
            "response": response_text,
            "risk_score": risk.score,
            "risk_tier": risk.tier,
            "agent": agent_name,
            **{k: v for k, v in result.items() if k != "response"},
        }

    async def _fetch_behavior(self, student_id: int) -> dict | None:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.post(
                    f"{MCP_STUDENT_URL}/tools/get_history",
                    json={"student_id": student_id, "days": 7},
                )
                r.raise_for_status()
                data = r.json()
                return data[0] if data else None
        except Exception as exc:
            logger.warning("Failed to fetch behavior for student %s: %s", student_id, exc)
            return None

    async def _fetch_skills(self, student_id: int) -> list[str]:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.post(
                    f"{MCP_STUDENT_URL}/tools/get_profile",
                    json={"student_id": student_id},
                )
                r.raise_for_status()
                profile = r.json()
                skills_raw = profile.get("skills", "")
                if isinstance(skills_raw, list):
                    return skills_raw
                return [s.strip() for s in skills_raw.split(",") if s.strip()]
        except Exception as exc:
            logger.warning("Failed to fetch skills for student %s: %s", student_id, exc)
            return []


_orchestrator: OrchestratorAgent | None = None


def get_orchestrator() -> OrchestratorAgent:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = OrchestratorAgent()
    return _orchestrator
