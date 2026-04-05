from fastapi import APIRouter, Depends, Request, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.database import get_db
from src.auth.dependencies import require_student, require_counselor
from src.auth.models import User
from src.wellbeing import schemas, service, models

router = APIRouter(prefix="/wellbeing", tags=["wellbeing"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/survey", response_model=schemas.RiskResult, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def submit_survey(
    request: Request,
    data: schemas.SurveySubmit,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    return await service.process_survey(db, current_user.id, data)


@router.get("/risk/{student_id}", response_model=schemas.WellbeingAlertResponse | None)
async def get_risk(
    student_id: int,
    current_user: User = Depends(require_counselor),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_latest_risk(db, student_id)


@router.post("/chat", response_model=schemas.ChatResponse)
@limiter.limit("30/minute")
async def chat(
    request: Request,
    data: schemas.ChatRequest,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    from agents.orchestrator.agent import get_orchestrator
    from src.students.service import get_student_by_user
    from src.wellbeing.service import seed_context_from_db, persist_chat_turn

    student = await get_student_by_user(db, current_user.id)

    # Restore conversation history from DB into the in-memory context store
    # so context survives server restarts
    await seed_context_from_db(db, student.id)

    orchestrator = get_orchestrator()
    result = await orchestrator.process(
        student_id=student.id,
        message=data.message,
    )

    # Persist both turns to DB for durability
    await persist_chat_turn(db, student.id, "user", data.message, risk_tier=result["risk_tier"])
    await persist_chat_turn(db, student.id, "assistant", result["response"], risk_tier=result["risk_tier"])

    # Create counselor alert for high/crisis risk — deduplicated to prevent spam
    risk_score = result.get("risk_score", 0)
    if risk_score and risk_score >= 0.6:
        from src.wellbeing.service import _has_recent_counselor_alert
        from src.counselor.models import CounselorAlert
        if not await _has_recent_counselor_alert(db, student.id):
            counselor_alert = CounselorAlert(
                student_id=student.id,
                risk_score=risk_score,
                anomaly_score=0.0,
                sentiment_score=0.0,
                survey_score=0.0,
                trigger_message=data.message,
            )
            db.add(counselor_alert)

    return schemas.ChatResponse(
        reply=result["response"],
        risk_tier=result["risk_tier"],
        risk_score=result.get("risk_score"),
        agent=result.get("agent"),
        helpline=result.get("helpline"),
    )


@router.post("/voice-chat", response_model=schemas.ChatResponse)
@limiter.limit("10/minute")
async def voice_chat(
    request: Request,
    audio: UploadFile = File(..., description="Audio file (WAV/MP3/OGG/WebM)"),
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Transcribe student audio via Whisper then process through the orchestrator."""
    _ALLOWED_AUDIO = {"audio/wav", "audio/mpeg", "audio/ogg", "audio/webm", "audio/mp4"}
    content_type = (audio.content_type or "").split(";")[0].strip()
    if content_type not in _ALLOWED_AUDIO:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported audio type '{content_type}'. Allowed: wav, mp3, ogg, webm.",
        )

    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Audio file is empty.")

    from ml.speech.transcriber import Transcriber
    transcriber = Transcriber()
    try:
        transcript = await transcriber.transcribe(audio_bytes)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transcription failed: {exc}",
        ) from exc

    if not transcript:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not extract speech from the audio file.",
        )

    from agents.orchestrator.agent import get_orchestrator
    from src.students.service import get_student_by_user

    student = await get_student_by_user(db, current_user.id)
    orchestrator = get_orchestrator()
    result = await orchestrator.process(
        student_id=student.id,
        message=transcript,
    )

    risk_score = result.get("risk_score", 0)
    if risk_score and risk_score >= 0.6:
        from src.wellbeing.service import _has_recent_counselor_alert
        from src.counselor.models import CounselorAlert
        if not await _has_recent_counselor_alert(db, student.id):
            counselor_alert = CounselorAlert(
                student_id=student.id,
                risk_score=risk_score,
                anomaly_score=0.0,
                sentiment_score=0.0,
                survey_score=0.0,
                trigger_message=transcript,
            )
            db.add(counselor_alert)
            await db.commit()

    return schemas.ChatResponse(
        reply=result["response"],
        risk_tier=result["risk_tier"],
        risk_score=result.get("risk_score"),
        agent=result.get("agent"),
        helpline=result.get("helpline"),
    )
