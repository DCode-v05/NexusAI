from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from src.wellbeing import models, schemas
from src.students.service import get_student_by_user, get_latest_behavior, get_mood_history, log_mood_survey
from src.students.schemas import MoodSurveyCreate
from src.shared.utils import utcnow

# Maximum chat turns to load from DB into the in-memory context store
_CONTEXT_LOAD_LIMIT = 10

# Minimum gap between counselor alerts for the same student — prevents duplicate spam
_ALERT_DEDUP_MINUTES = 15


async def seed_context_from_db(db: AsyncSession, student_id: int) -> None:
    """Load the last N chat turns from DB into the in-memory context store.

    Called at the start of each chat request to ensure the context store is
    warm even after a server restart.  Already-loaded turns are skipped via the
    existing deque (no double-loading).
    """
    from agents.orchestrator.context_store import get_context_store
    ctx = get_context_store()

    # If we already have turns in memory for this student, don't re-load
    if ctx.get_history(student_id):
        return

    result = await db.execute(
        select(models.ChatMessage)
        .where(models.ChatMessage.student_id == student_id)
        .order_by(desc(models.ChatMessage.created_at))
        .limit(_CONTEXT_LOAD_LIMIT)
    )
    rows = list(result.scalars().all())
    # Rows are newest-first; reverse to chronological order for appending
    for row in reversed(rows):
        ctx.append(student_id, row.role, row.content, risk_tier=row.risk_tier)


async def persist_chat_turn(
    db: AsyncSession,
    student_id: int,
    role: str,
    content: str,
    risk_tier: str = "low",
) -> None:
    """Persist a single chat turn to the DB."""
    msg = models.ChatMessage(
        student_id=student_id,
        role=role,
        content=content,
        risk_tier=risk_tier,
    )
    db.add(msg)
    # Commit is handled by the router's get_db dependency


async def get_latest_risk(db: AsyncSession, student_id: int) -> models.WellbeingAlert | None:
    result = await db.execute(
        select(models.WellbeingAlert)
        .where(models.WellbeingAlert.student_id == student_id)
        .order_by(desc(models.WellbeingAlert.created_at))
        .limit(1)
    )
    return result.scalar_one_or_none()


async def store_alert(db: AsyncSession, student_id: int, risk: schemas.RiskResult) -> models.WellbeingAlert:
    alert = models.WellbeingAlert(
        student_id=student_id,
        risk_score=risk.score,
        anomaly_score=risk.anomaly_score,
        sentiment_score=risk.sentiment_score,
        survey_decline=risk.survey_decline,
        tier=risk.tier,
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return alert


async def _has_recent_counselor_alert(db: AsyncSession, student_id: int) -> bool:
    """Return True if an unresolved counselor alert exists within the dedup window."""
    from src.counselor.models import CounselorAlert
    threshold = utcnow() - timedelta(minutes=_ALERT_DEDUP_MINUTES)
    result = await db.execute(
        select(CounselorAlert)
        .where(
            CounselorAlert.student_id == student_id,
            CounselorAlert.is_resolved == False,  # noqa: E712
            CounselorAlert.created_at >= threshold,
        )
        .limit(1)
    )
    return result.scalar_one_or_none() is not None


async def process_survey(
    db: AsyncSession,
    user_id: int,
    data: schemas.SurveySubmit,
) -> schemas.RiskResult:
    """Submit mood survey, compute risk, store alert if needed."""
    from ml.risk.scorer import RiskScorer
    from ml.anomaly.detector import AnomalyDetector
    from ml.sentiment.analyzer import SentimentAnalyzer

    student = await get_student_by_user(db, user_id)

    # 1. Store mood survey
    survey_data = MoodSurveyCreate(
        q1_score=data.q1_score,
        q2_score=data.q2_score,
        q3_score=data.q3_score,
        free_text=data.free_text,
    )
    survey = await log_mood_survey(db, student.id, survey_data)

    # 2. Compute anomaly score from latest behavior log
    behavior = await get_latest_behavior(db, student.id)
    anomaly_score = 0.0
    if behavior:
        detector = AnomalyDetector()
        anomaly_score = await detector.predict_from_log(behavior)

    # 3. Compute sentiment score from free text
    sentiment_score = 0.0
    if data.free_text:
        analyzer = SentimentAnalyzer()
        sentiment_score = await analyzer.analyze(data.free_text)

    # 4. Compute survey decline vs previous (fixed: use indices 1..3 of sorted history)
    history = await get_mood_history(db, student.id, days=7)
    survey_decline = 0.0
    # history[0] is the survey we just inserted; compare against up to 3 prior surveys
    prior = [s for s in history if s.id != survey.id][:3]
    if prior:
        prev_avg = sum(s.composite_score for s in prior) / len(prior)
        current = survey.composite_score
        survey_decline = max(0.0, (prev_avg - current) / 10.0)

    # 5. Compute weighted risk: 0.50*anomaly + 0.35*sentiment + 0.15*survey_decline
    scorer = RiskScorer()
    risk = scorer.compute(anomaly_score, sentiment_score, survey_decline)

    # 6. Store wellbeing alert if meaningful risk
    if risk.score >= 0.4:
        await store_alert(db, student.id, risk)

    # 7. Create counselor alert for high/crisis risk — deduplicated by 15-min window
    if risk.score >= 0.6:
        if not await _has_recent_counselor_alert(db, student.id):
            from src.counselor.models import CounselorAlert
            counselor_alert = CounselorAlert(
                student_id=student.id,
                risk_score=risk.score,
                anomaly_score=risk.anomaly_score,
                sentiment_score=risk.sentiment_score,
                survey_score=survey.composite_score,
                trigger_message=data.free_text or (
                    f"Survey: q1={data.q1_score}/10, q2={data.q2_score}/10, q3={data.q3_score}/10"
                ),
            )
            db.add(counselor_alert)
            await db.commit()

    return risk
