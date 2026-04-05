from fastapi import APIRouter, Depends, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.auth.dependencies import require_student
from src.auth.models import User
from src.pathway import schemas, service

router = APIRouter(prefix="/pathway", tags=["pathway"])


@router.post("/resume", response_model=schemas.SkillProfileResponse)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    file_bytes = await file.read()
    return await service.parse_resume(db, current_user.id, file_bytes)


@router.post("/generate-roadmap", response_model=schemas.RoadmapResponse, status_code=status.HTTP_201_CREATED)
async def generate_roadmap(
    data: schemas.GenerateRoadmapRequest,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    return await service.generate_roadmap(db, current_user.id, data)


@router.post("/job-openings")
async def get_job_openings(
    data: schemas.JobOpeningsRequest,
    current_user: User = Depends(require_student),
):
    """Fetch job openings from MCP job-market server."""
    import httpx
    from src.config import settings
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                f"{settings.MCP_JOB_MARKET_URL}/tools/get_top_roles",
                json={"skills": data.skills, "limit": 10},
            )
            r.raise_for_status()
            return r.json()
    except Exception:
        return []


@router.get("/mock-interview/{role}", response_model=schemas.MockInterviewResponse)
async def mock_interview(
    role: str,
    current_user: User = Depends(require_student),
):
    from agents.pathway.agent import get_pathway_agent

    agent = get_pathway_agent()
    question = await agent.mock_interview(role)
    return schemas.MockInterviewResponse(question=question)


@router.post("/mock-interview/start", response_model=schemas.MockInterviewStartResponse)
async def mock_interview_start(
    data: schemas.GenerateRoadmapRequest,  # reuse target_role field
    current_user: User = Depends(require_student),
):
    """Start a new multi-turn mock interview session. Returns session_id and Q1."""
    from agents.pathway.agent import get_pathway_agent
    from agents.interview_store import get_interview_store

    store = get_interview_store()
    session = store.create(role=data.target_role)

    agent = get_pathway_agent()
    question_text = await agent.mock_interview(data.target_role)

    session.question_num = 1
    session.append_interviewer(question_text)

    return schemas.MockInterviewStartResponse(
        session_id=session.session_id,
        role=session.role,
        question_num=session.question_num,
        total_questions=session.total_questions,
        question=question_text,
    )


@router.post("/mock-interview/answer", response_model=schemas.MockInterviewAnswerResponse)
async def mock_interview_answer(
    data: schemas.MockInterviewAnswerRequest,
    current_user: User = Depends(require_student),
):
    """Submit an answer; receive feedback and the next question (or closing summary)."""
    from fastapi import HTTPException
    from agents.pathway.agent import get_pathway_agent
    from agents.interview_store import get_interview_store

    store = get_interview_store()
    session = store.get(data.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found or expired.")
    if session.is_complete:
        raise HTTPException(status_code=400, detail="This interview session has already ended.")

    session.append_candidate(data.answer)

    agent = get_pathway_agent()
    history = session.format_history()

    is_last = session.question_num >= session.total_questions

    if is_last:
        # Final question answered — ask for closing feedback
        feedback_prompt = (
            f"The candidate has just answered question {session.question_num} of {session.total_questions} "
            f"for the role '{session.role}'. Provide brief, encouraging feedback on their answer, "
            "then give an overall interview summary with 2–3 actionable improvement tips."
        )
        feedback = await agent.answer_question(feedback_prompt, history)
        session.append_interviewer(feedback)
        session.is_complete = True
        next_question = None
    else:
        # Mid-interview — give feedback then ask next question
        next_num = session.question_num + 1
        feedback_prompt = (
            f"The candidate answered question {session.question_num} of {session.total_questions} "
            f"for the role '{session.role}'. Give brief feedback (2–3 sentences), "
            f"then ask question {next_num} of {session.total_questions}."
        )
        combined = await agent.answer_question(feedback_prompt, history)
        # Split feedback from next question heuristically on newline boundary
        parts = combined.split("\n\n", 1)
        feedback = parts[0].strip()
        next_question = parts[1].strip() if len(parts) > 1 else combined

        session.append_interviewer(combined)
        session.question_num = next_num

    return schemas.MockInterviewAnswerResponse(
        session_id=session.session_id,
        question_num=session.question_num,
        total_questions=session.total_questions,
        feedback=feedback,
        next_question=next_question,
        is_complete=session.is_complete,
    )


@router.get("/profile", response_model=schemas.SkillProfileResponse)
async def get_profile(
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    from src.students.service import get_student_by_user

    student = await get_student_by_user(db, current_user.id)
    return await service.get_or_create_skill_profile(db, student.id)
