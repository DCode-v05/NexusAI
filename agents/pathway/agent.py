"""PathwayAgent — skill gap analysis + RAG + 12-week roadmap + mock interview."""
from __future__ import annotations

import httpx

from agents.llm import get_llm_router

from src.config import settings

MCP_JOB_URL = settings.MCP_JOB_MARKET_URL
MCP_RAG_URL = settings.MCP_RESOURCE_RAG_URL

ROADMAP_SYSTEM = (
    "You are NexusAI's career guidance AI for Indian engineering students. "
    "Create a detailed, actionable 12-week career roadmap based on the student's "
    "current skills, target role, and available resources. "
    "Structure the roadmap with weekly goals, specific resources (course names, links if known), "
    "and measurable milestones. Focus on practical, achievable steps. "
    "Use Indian job market context (TCS, Infosys, startups, MAANG India offices). "
    "Do NOT include any PII."
)

CHAT_SYSTEM = (
    "You are NexusAI's career guidance AI for Indian college students. "
    "Provide helpful, actionable career advice including job market insights, "
    "skill recommendations, course suggestions (SWAYAM, Coursera, NPTEL), "
    "government schemes (PMKVY, Digital India), interview tips, and resume guidance. "
    "Keep responses concise and encouraging. Use Indian job market context. "
    "If the student seems distressed, gently acknowledge it and suggest they try the MindBridge module. "
    "Do NOT include any PII."
)

MOCK_INTERVIEW_SYSTEM = (
    "You are an experienced technical interviewer at a top Indian tech company. "
    "Conduct a realistic mock interview for the given role. "
    "Ask 5 progressive questions: 2 conceptual, 2 practical/coding, 1 situational. "
    "After each question, wait for the answer or provide model answers. "
    "Give constructive feedback. Be professional but encouraging. "
    "Do NOT include any PII."
)


class PathwayAgent:
    def __init__(self):
        self._llm = get_llm_router()

    async def generate_roadmap(
        self,
        current_skills: list[str],
        target_role: str,
        history: str = "",
    ) -> str:
        job_data = await self._fetch_job_market(current_skills, target_role)
        resources = await self._fetch_resources(target_role, current_skills)

        prompt = self._build_roadmap_prompt(
            current_skills, target_role, job_data, resources, history
        )
        return await self._llm.generate(prompt, ROADMAP_SYSTEM)

    async def chat(self, message: str, history: str = "") -> str:
        """Conversational career guidance — used by unified chat."""
        prompt = message
        if history:
            prompt = f"Conversation so far:\n{history}\n\nStudent: {message}"
        return await self._llm.generate(prompt, CHAT_SYSTEM)

    async def mock_interview(self, role: str) -> str:
        prompt = (
            f"Start a mock interview for the role: {role}. "
            "Introduce yourself as the interviewer and ask the first question."
        )
        return await self._llm.generate(prompt, MOCK_INTERVIEW_SYSTEM)

    async def answer_question(self, question: str, history: str = "") -> str:
        prompt = question
        if history:
            prompt = f"Interview so far:\n{history}\n\nCandidate: {question}"
        return await self._llm.generate(prompt, MOCK_INTERVIEW_SYSTEM)

    async def _fetch_job_market(
        self, skills: list[str], role: str
    ) -> dict:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.post(
                    f"{MCP_JOB_URL}/tools/get_top_roles",
                    json={"skills": skills, "limit": 5},
                )
                r.raise_for_status()
                return {"jobs": r.json(), "role": role}
        except Exception:
            return {"jobs": [], "role": role}

    async def _fetch_resources(
        self, domain: str, skills: list[str]
    ) -> list[dict]:
        query = f"{domain} {' '.join(skills[:3])}"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.post(
                    f"{MCP_RAG_URL}/tools/search_resources",
                    json={"query": query, "top_k": 8, "domain_filter": None},
                )
                r.raise_for_status()
                return r.json()
        except Exception:
            return []

    def _build_roadmap_prompt(
        self,
        skills: list[str],
        role: str,
        job_data: dict,
        resources: list[dict],
        history: str,
    ) -> str:
        skills_str = ", ".join(skills) if skills else "not specified"
        jobs_str = ""
        if job_data.get("jobs"):
            top = job_data["jobs"][:3]
            jobs_str = "\n".join(
                f"- {j.get('role', 'N/A')} at {j.get('company', 'N/A')}: requires {', '.join(j.get('required_skills', [])[:4])}"
                for j in top
            )

        resources_str = ""
        if resources:
            resources_str = "\n".join(
                f"- [{r.get('type', 'course')}] {r.get('title', '')}: {r.get('url', '')}"
                for r in resources[:6]
            )

        parts = [
            f"Student's current skills: {skills_str}",
            f"Target role: {role}",
        ]
        if jobs_str:
            parts.append(f"Top job market requirements:\n{jobs_str}")
        if resources_str:
            parts.append(f"Available learning resources:\n{resources_str}")
        if history:
            parts.append(f"Prior conversation:\n{history}")
        parts.append(
            "Create a 12-week roadmap with weekly milestones, specific resources, and skill targets."
        )
        return "\n\n".join(parts)


_agent: PathwayAgent | None = None


def get_pathway_agent() -> PathwayAgent:
    global _agent
    if _agent is None:
        _agent = PathwayAgent()
    return _agent
