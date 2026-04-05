from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.auth.dependencies import require_student
from src.auth.models import User
from src.students import schemas, service

router = APIRouter(prefix="/students", tags=["students"])


@router.post("/profile", response_model=schemas.StudentResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    data: schemas.StudentCreate,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_or_create_student(db, current_user.id, data)


@router.get("/me", response_model=schemas.StudentResponse)
async def get_my_profile(
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_student_by_user(db, current_user.id)


@router.get("/dashboard", response_model=schemas.StudentDashboardResponse)
async def get_dashboard(
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_dashboard(db, current_user.id)


@router.post("/behavior-log", response_model=schemas.BehaviorLogResponse, status_code=status.HTTP_201_CREATED)
async def log_behavior(
    data: schemas.BehaviorLogCreate,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    student = await service.get_student_by_user(db, current_user.id)
    return await service.update_behavior_log(db, student.id, data)


@router.get("/mood-history")
async def mood_history(
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    student = await service.get_student_by_user(db, current_user.id)
    history = await service.get_mood_history(db, student.id, days=30)
    return [
        {"date": m.submitted_at.date().isoformat(), "composite": m.composite_score}
        for m in history
    ]
