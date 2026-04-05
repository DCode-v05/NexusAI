"""WellbeingAgent — empathetic response calibrated to risk tier."""
from __future__ import annotations

from agents.llm import get_llm_router

SYSTEM_PROMPTS = {
    "low": (
        "You are NexusAI's wellbeing companion. The student appears to be doing well. "
        "Respond warmly, acknowledge their feelings, and offer light encouragement. "
        "Keep responses concise and supportive. Do NOT include any PII."
    ),
    "moderate": (
        "You are NexusAI's wellbeing companion. The student may be experiencing some stress. "
        "Respond with empathy and validate their feelings. Gently suggest healthy coping strategies "
        "such as talking to friends, taking breaks, or using campus counseling resources. "
        "Keep responses supportive and non-judgmental. Do NOT include any PII."
    ),
    "high": (
        "You are NexusAI's wellbeing companion. The student is showing signs of significant distress. "
        "Respond with deep empathy. Acknowledge their pain. Strongly encourage them to speak with "
        "a counselor or trusted person. Mention iCall helpline: 9152987821. "
        "Do NOT minimize their feelings. Do NOT include any PII."
    ),
    "crisis": (
        "You are NexusAI's wellbeing companion. This student may be in crisis. "
        "Respond with utmost care and compassion. Tell them they are not alone. "
        "Provide the iCall helpline number: 9152987821 prominently. "
        "Encourage immediate contact with a counselor. Do NOT include any PII."
    ),
}


class WellbeingAgent:
    def __init__(self):
        self._llm = get_llm_router()

    async def respond(
        self,
        message: str,
        risk_tier: str,
        history: str = "",
    ) -> str:
        system = SYSTEM_PROMPTS.get(risk_tier, SYSTEM_PROMPTS["moderate"])
        prompt = message
        if history:
            prompt = f"Conversation history:\n{history}\n\nStudent: {message}"
        return await self._llm.generate(prompt, system)


_agent: WellbeingAgent | None = None


def get_wellbeing_agent() -> WellbeingAgent:
    global _agent
    if _agent is None:
        _agent = WellbeingAgent()
    return _agent
