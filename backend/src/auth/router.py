from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from src.database import get_db
from src.auth import schemas, models, service
from src.auth.dependencies import get_current_user, oauth2_scheme

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def register(request: Request, user_in: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.User).where(models.User.email == user_in.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = models.User(
        email=user_in.email,
        hashed_password=service.hash_password(user_in.password),
        role=user_in.role,
    )
    db.add(user)
    await db.flush()

    # Auto-create student profile for student users
    if user_in.role == models.UserRole.student:
        from src.students.models import Student

        name = user_in.email.split("@")[0].replace(".", " ").title()
        student = Student(user_id=user.id, name=name)
        db.add(student)

    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=schemas.Token)
@limiter.limit("5/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(models.User).where(models.User.email == form_data.username))
    user = result.scalar_one_or_none()

    if not user or not service.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    token_data = {"sub": str(user.id), "role": user.role.value}
    access_token = service.create_access_token(data=token_data)
    refresh_token = service.create_refresh_token(data=token_data)
    return schemas.Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=schemas.Token)
async def refresh(body: schemas.RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Issue new access + refresh tokens from a valid refresh token."""
    payload = service.decode_token(body.refresh_token)

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    # Check if this refresh token has been revoked
    jti = payload.get("jti")
    if jti:
        result = await db.execute(
            select(models.RevokedToken).where(models.RevokedToken.jti == jti)
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked")

    # Revoke the used refresh token (rotate — one-time use)
    if jti:
        exp_ts = payload.get("exp", 0)
        expires_at = datetime.fromtimestamp(exp_ts, tz=timezone.utc).replace(tzinfo=None)
        db.add(models.RevokedToken(jti=jti, expires_at=expires_at))
        await db.commit()

    # Issue fresh token pair
    token_data = {"sub": payload["sub"], "role": payload["role"]}
    access_token = service.create_access_token(data=token_data)
    new_refresh_token = service.create_refresh_token(data=token_data)
    return schemas.Token(access_token=access_token, refresh_token=new_refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    """Revoke the current access token so it cannot be reused."""
    payload = service.decode_token(token)
    if payload and (jti := payload.get("jti")):
        exp_ts = payload.get("exp", 0)
        expires_at = datetime.fromtimestamp(exp_ts, tz=timezone.utc).replace(tzinfo=None)
        # Only insert if not already revoked (idempotent logout)
        existing = await db.execute(
            select(models.RevokedToken).where(models.RevokedToken.jti == jti)
        )
        if not existing.scalar_one_or_none():
            db.add(models.RevokedToken(jti=jti, expires_at=expires_at))
            await db.commit()


@router.get("/me", response_model=schemas.UserResponse)
async def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user
