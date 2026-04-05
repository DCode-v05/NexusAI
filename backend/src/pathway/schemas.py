from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class SkillProfileResponse(BaseModel):
    id: int
    student_id: int
    skills: list[str]
    target_role: str | None
    target_location: str | None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RoadmapWeek(BaseModel):
    week: int
    title: str = ""
    theme: str = ""
    tasks: list[str] = []
    resources: list[dict] = []
    milestone: str = ""


class RoadmapResponse(BaseModel):
    id: int
    target_role: str
    roadmap: str = ""        # Raw LLM text
    weeks: list[RoadmapWeek] = []
    skill_gaps: list[str] = []
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MockInterviewQuestion(BaseModel):
    question: str
    category: str  # "technical" | "behavioral"
    hints: list[str]


class MockInterviewResponse(BaseModel):
    question: str
    role: str = ""
    questions: list[MockInterviewQuestion] = []


class MockInterviewStartResponse(BaseModel):
    session_id: str
    role: str
    question_num: int
    total_questions: int
    question: str


class MockInterviewAnswerRequest(BaseModel):
    session_id: str
    answer: str


class MockInterviewAnswerResponse(BaseModel):
    session_id: str
    question_num: int
    total_questions: int
    feedback: str
    next_question: str | None   # None when interview is complete
    is_complete: bool


class GenerateRoadmapRequest(BaseModel):
    target_role: str = Field(..., min_length=1, max_length=200)
    target_location: str = Field("India", max_length=200)


class JobOpeningsRequest(BaseModel):
    skills: list[str] = []
    target_role: str = "Software Engineer"
