from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.exc import IntegrityError

from src.students import models, schemas
from src.shared.exceptions import NotFoundError


async def get_or_create_student(db: AsyncSession, user_id: int, data: schemas.StudentCreate) -> models.Student:
    result = await db.execute(select(models.Student).where(models.Student.user_id == user_id))
    student = result.scalar_one_or_none()
    if student:
        return student

    try:
        student = models.Student(user_id=user_id, **data.model_dump())
        db.add(student)
        await db.commit()
        await db.refresh(student)
        return student
    except IntegrityError:
        # Another concurrent request created the row first — re-fetch
        await db.rollback()
        result = await db.execute(select(models.Student).where(models.Student.user_id == user_id))
        return result.scalar_one()


async def get_student_by_user(db: AsyncSession, user_id: int) -> models.Student:
    result = await db.execute(select(models.Student).where(models.Student.user_id == user_id))
    student = result.scalar_one_or_none()
    if not student:
        # Auto-create student profile from user record
        from src.auth.models import User

        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise NotFoundError("User")
        name = user.email.split("@")[0].replace(".", " ").title()
        try:
            student = models.Student(user_id=user_id, name=name)
            db.add(student)
            await db.commit()
            await db.refresh(student)
        except IntegrityError:
            # Concurrent request created the row — re-fetch
            await db.rollback()
            result = await db.execute(select(models.Student).where(models.Student.user_id == user_id))
            student = result.scalar_one()
    return student


async def get_student_by_id(db: AsyncSession, student_id: int) -> models.Student:
    result = await db.execute(select(models.Student).where(models.Student.id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        raise NotFoundError("Student")
    return student


async def update_behavior_log(
    db: AsyncSession, student_id: int, data: schemas.BehaviorLogCreate
) -> models.BehaviorLog:
    log = models.BehaviorLog(student_id=student_id, **data.model_dump())
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


async def get_latest_behavior(db: AsyncSession, student_id: int) -> models.BehaviorLog | None:
    result = await db.execute(
        select(models.BehaviorLog)
        .where(models.BehaviorLog.student_id == student_id)
        .order_by(desc(models.BehaviorLog.logged_at))
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_mood_history(db: AsyncSession, student_id: int, days: int = 30) -> list[models.MoodSurvey]:
    result = await db.execute(
        select(models.MoodSurvey)
        .where(models.MoodSurvey.student_id == student_id)
        .order_by(desc(models.MoodSurvey.submitted_at))
        .limit(days)
    )
    return list(result.scalars().all())


async def log_mood_survey(
    db: AsyncSession, student_id: int, data: schemas.MoodSurveyCreate
) -> models.MoodSurvey:
    composite = (data.q1_score + data.q2_score + data.q3_score) / 3.0
    survey = models.MoodSurvey(
        student_id=student_id,
        composite_score=composite,
        **data.model_dump(),
    )
    db.add(survey)
    await db.commit()
    await db.refresh(survey)
    return survey


async def get_dashboard(db: AsyncSession, user_id: int) -> schemas.StudentDashboardResponse:
    student = await get_student_by_user(db, user_id)
    latest_behavior = await get_latest_behavior(db, student.id)
    mood_history = await get_mood_history(db, student.id, days=30)

    # Simple streak: count consecutive days with a mood survey
    streak = 0
    if mood_history:
        from datetime import date, timedelta
        today = date.today()
        for i, survey in enumerate(mood_history):
            expected = today - timedelta(days=i)
            if survey.submitted_at.date() == expected:
                streak += 1
            else:
                break

    return schemas.StudentDashboardResponse(
        profile=schemas.StudentResponse.model_validate(student),
        latest_behavior=schemas.BehaviorLogResponse.model_validate(latest_behavior) if latest_behavior else None,
        mood_history=[schemas.MoodSurveyResponse.model_validate(s) for s in mood_history],
        login_streak=streak,
    )
