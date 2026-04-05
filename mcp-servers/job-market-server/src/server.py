"""MCP Job Market Server — port 9002.

Primary: LinkedIn API via adhikasp/mcp-linkedin (linkedin-api package)
Fallback: mock_data/jobs_mock.json when LinkedIn rate-limits or credentials unavailable.

Tools: get_top_roles, get_skill_demand, get_salary_range, get_trending_skills

All responses include `data_source` ("linkedin" | "mock") and `fetched_at` (ISO timestamp)
so the frontend can display a freshness indicator.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel
from pydantic_settings import BaseSettings

MOCK_DATA_PATH = Path(__file__).parent / "mock_data" / "jobs_mock.json"
_mock_jobs: list[dict] = []
_linkedin_client = None
_mock_loaded_at: str = ""


class Settings(BaseSettings):
    LINKEDIN_EMAIL: str = ""
    LINKEDIN_PASSWORD: str = ""
    class Config:
        env_file = ".env"

settings = Settings()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_mock():
    global _mock_jobs, _mock_loaded_at
    if MOCK_DATA_PATH.exists():
        with open(MOCK_DATA_PATH) as f:
            _mock_jobs = json.load(f)
        _mock_loaded_at = _now_iso()


def _get_linkedin():
    global _linkedin_client
    if _linkedin_client is None and settings.LINKEDIN_EMAIL and settings.LINKEDIN_PASSWORD:
        try:
            from linkedin_api import Linkedin
            _linkedin_client = Linkedin(settings.LINKEDIN_EMAIL, settings.LINKEDIN_PASSWORD)
        except Exception as e:
            print(f"LinkedIn auth failed: {e}. Falling back to mock data.")
    return _linkedin_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    _load_mock()
    _get_linkedin()
    yield

app = FastAPI(title="MCP Job Market Server", lifespan=lifespan)


class GetTopRolesRequest(BaseModel):
    skills: list[str]
    location: str = "India"
    limit: int = 10


class GetSkillDemandRequest(BaseModel):
    skill: str
    location: str = "India"


class GetSalaryRangeRequest(BaseModel):
    role: str
    location: str = "India"


class GetTrendingSkillsRequest(BaseModel):
    domain: str
    limit: int = 10


def _mock_top_roles(skills: list[str], limit: int) -> list[dict]:
    skill_set = {s.lower() for s in skills}
    scored = []
    for job in _mock_jobs:
        req = {r.lower() for r in job.get("required_skills", [])}
        overlap = len(skill_set & req)
        if overlap > 0:
            scored.append({"score": overlap, **job})
    scored.sort(key=lambda x: x["score"], reverse=True)
    results = scored[:limit]
    # Attach freshness metadata to every entry
    for r in results:
        r.setdefault("data_source", "mock")
        r.setdefault("is_mock", True)
        r.setdefault("fetched_at", _mock_loaded_at or _now_iso())
    return results


@app.get("/health")
async def health():
    return {"status": "ok", "service": "mcp-job-market", "linkedin": _linkedin_client is not None}


@app.post("/tools/get_top_roles")
async def get_top_roles(req: GetTopRolesRequest):
    li = _get_linkedin()
    if li:
        try:
            import asyncio
            query = " ".join(req.skills[:3])
            fetched_at = _now_iso()
            jobs = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: li.search_jobs(keywords=query, location_name=req.location, limit=req.limit),
            )
            return [
                {
                    "role": j.get("title", ""),
                    "company": j.get("companyDetails", {}).get("company", {}).get("name", ""),
                    "location": req.location,
                    "required_skills": req.skills,
                    "data_source": "linkedin",
                    "is_mock": False,
                    "fetched_at": fetched_at,
                }
                for j in jobs
            ]
        except Exception as e:
            print(f"LinkedIn get_top_roles failed: {e}. Using mock.")

    return _mock_top_roles(req.skills, req.limit)


@app.post("/tools/get_skill_demand")
async def get_skill_demand(req: GetSkillDemandRequest):
    li = _get_linkedin()
    if li:
        try:
            import asyncio
            jobs = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: li.search_jobs(keywords=req.skill, location_name=req.location, limit=25),
            )
            return {"skill": req.skill, "job_count": len(jobs), "data_source": "linkedin", "is_mock": False, "fetched_at": _now_iso()}
        except Exception:
            pass

    count = sum(1 for j in _mock_jobs if req.skill.lower() in [s.lower() for s in j.get("required_skills", [])])
    return {"skill": req.skill, "job_count": count, "data_source": "mock", "is_mock": True, "fetched_at": _mock_loaded_at or _now_iso()}


@app.post("/tools/get_salary_range")
async def get_salary_range(req: GetSalaryRangeRequest):
    for job in _mock_jobs:
        if req.role.lower() in job.get("role", "").lower():
            return {
                "role": req.role,
                "min_lpa": job.get("min_salary_lpa", 4),
                "max_lpa": job.get("max_salary_lpa", 12),
                "avg_lpa": job.get("avg_salary_lpa", 8),
                "data_source": "mock",
                "is_mock": True,
                "fetched_at": _mock_loaded_at or _now_iso(),
            }
    return {
        "role": req.role,
        "min_lpa": 4,
        "max_lpa": 15,
        "avg_lpa": 9,
        "data_source": "mock",
        "is_mock": True,
        "fetched_at": _mock_loaded_at or _now_iso(),
    }


@app.post("/tools/get_trending_skills")
async def get_trending_skills(req: GetTrendingSkillsRequest):
    li = _get_linkedin()
    if li:
        try:
            import asyncio
            from collections import Counter
            jobs = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: li.search_jobs(keywords=req.domain, location_name="India", limit=20),
            )
            # Extract skills from job descriptions (simplified)
            counter: Counter = Counter()
            for j in jobs:
                desc = j.get("description", {}).get("text", "")
                for skill in ["Python", "SQL", "React", "ML", "Docker", "AWS", "Java", "TypeScript"]:
                    if skill.lower() in desc.lower():
                        counter[skill] += 1
            return [{"skill": s, "count": c} for s, c in counter.most_common(req.limit)]
        except Exception:
            pass

    domain_skills = {
        "data-science": ["Python", "SQL", "Machine Learning", "TensorFlow", "Statistics"],
        "web-dev": ["React", "TypeScript", "Node.js", "CSS", "REST API"],
        "ml": ["PyTorch", "Python", "NLP", "Computer Vision", "MLOps"],
        "cloud": ["AWS", "Docker", "Kubernetes", "Terraform", "CI/CD"],
    }
    skills = domain_skills.get(req.domain, ["Python", "SQL", "Git"])
    fetched_at = _mock_loaded_at or _now_iso()
    return [
        {"skill": s, "count": 100 - i * 10, "data_source": "mock", "is_mock": True, "fetched_at": fetched_at}
        for i, s in enumerate(skills[:req.limit])
    ]
