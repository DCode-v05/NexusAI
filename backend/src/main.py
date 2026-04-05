from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from src.config import settings
from src.database import engine, Base

# Import all models so Base.metadata is populated
import src.auth.models  # noqa: F401
import src.students.models  # noqa: F401
import src.wellbeing.models  # noqa: F401  (registers WellbeingAlert + ChatMessage)
import src.pathway.models  # noqa: F401
import src.counselor.models  # noqa: F401

from src.auth.router import router as auth_router
from src.students.router import router as students_router
from src.wellbeing.router import router as wellbeing_router
from src.pathway.router import router as pathway_router
from src.counselor.router import router as counselor_router

# Rate limiter — keyed by client IP
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    import asyncio

    for attempt in range(5):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            break
        except Exception as e:
            if attempt < 4:
                print(f"DB connection attempt {attempt + 1} failed: {e}, retrying in 3s...")
                await asyncio.sleep(3)
            else:
                raise

    # Clean up expired revoked tokens so the blacklist table doesn't grow unbounded
    await _cleanup_expired_revoked_tokens()

    # Ensure RAG FAISS index exists (auto-builds on first run)
    await _ensure_rag_index()

    # Pre-warm ML models in background so first request is fast
    async def _warmup():
        try:
            loop = asyncio.get_event_loop()
            print("Pre-warming ML models...")
            from ml.sentiment.analyzer import SentimentAnalyzer
            sa = SentimentAnalyzer()
            await loop.run_in_executor(None, sa._analyze_sync, "test")
            print("ML models loaded.")
        except Exception as e:
            print(f"ML warmup failed (non-fatal): {e}")

    asyncio.create_task(_warmup())

    # Periodically evict stale context store entries (every 30 min)
    async def _context_gc():
        while True:
            await asyncio.sleep(1800)  # 30 minutes
            try:
                from agents.orchestrator.context_store import get_context_store
                n = get_context_store().evict_stale()
                if n:
                    print(f"Context store GC: evicted {n} stale student session(s).")
            except Exception as e:
                print(f"Context GC failed (non-fatal): {e}")

    asyncio.create_task(_context_gc())

    yield


async def _ensure_rag_index():
    """Trigger FAISS index build on first startup if the index file is missing."""
    try:
        import sys
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))

        from rag.indexer import INDEX_PATH
        if not INDEX_PATH.exists():
            print("RAG index missing — building in background...")
            from rag.scripts.build_index import build
            import asyncio
            asyncio.create_task(build())
        else:
            print("RAG index already present.")
    except Exception as e:
        print(f"RAG index check failed (non-fatal): {e}")


async def _cleanup_expired_revoked_tokens():
    """Delete revoked tokens whose JWT expiry has already passed — safe to remove."""
    try:
        from sqlalchemy import delete
        from src.auth.models import RevokedToken
        from src.database import async_session
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        async with async_session() as db:
            await db.execute(delete(RevokedToken).where(RevokedToken.expires_at < now))
            await db.commit()
        print("Expired revoked tokens cleaned up.")
    except Exception as e:
        print(f"Token cleanup failed (non-fatal): {e}")


app = FastAPI(
    title="NexusAI API",
    description="Academic Wellbeing & Career Co-Pilot",
    version="0.1.0",
    lifespan=lifespan,
)

# Attach rate limiter state and exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS — only allow the configured frontend origin (not wildcard)
allowed_origins = list({settings.FRONTEND_URL, "http://localhost:3000"})
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

app.add_middleware(
    OriginValidationMiddleware,
    allowed_origins=set(allowed_origins),
)


_CSRF_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
_CSRF_EXEMPT_PATHS = {"/health", "/auth/login", "/auth/register", "/auth/refresh"}


class OriginValidationMiddleware(BaseHTTPMiddleware):
    """Validate the Origin header on state-changing requests as CSRF defence-in-depth.

    Since NexusAI uses Authorization: Bearer tokens (not cookies), classical
    CSRF is not exploitable. This middleware adds a secondary layer: browsers
    always send Origin on cross-origin state-changing requests, so verifying it
    blocks any future cookie-based auth path and provides defence against other
    cross-origin attack vectors.

    Rules:
    - Safe methods (GET, HEAD, OPTIONS) and preflight are always allowed.
    - Requests without an Origin header (e.g. server-to-server, curl) are allowed.
    - If Origin is present, it must match an allowed frontend origin.
    """

    def __init__(self, app, allowed_origins: set[str]):
        super().__init__(app)
        self._allowed = allowed_origins

    async def dispatch(self, request: Request, call_next):
        if request.method in _CSRF_SAFE_METHODS:
            return await call_next(request)
        if request.url.path in _CSRF_EXEMPT_PATHS:
            return await call_next(request)

        origin = request.headers.get("origin")
        if origin and origin not in self._allowed:
            return JSONResponse(
                status_code=403,
                content={"detail": f"Origin '{origin}' is not allowed."},
            )
        return await call_next(request)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": str(exc.body)},
    )


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "service": "nexusai-backend"}


app.include_router(auth_router)
app.include_router(students_router)
app.include_router(wellbeing_router)
app.include_router(pathway_router)
app.include_router(counselor_router)
