from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.database import get_db
from src.auth import service, models

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = service.decode_token(token)
    if payload is None:
        raise credentials_exception

    # Reject refresh tokens used as access tokens
    if payload.get("type") != "access":
        raise credentials_exception

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    # Check token blacklist
    jti = payload.get("jti")
    if jti:
        revoked = await db.execute(
            select(models.RevokedToken).where(models.RevokedToken.jti == jti)
        )
        if revoked.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )

    result = await db.execute(select(models.User).where(models.User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise credentials_exception
    return user


async def require_student(current_user: models.User = Depends(get_current_user)) -> models.User:
    if current_user.role not in (models.UserRole.student, models.UserRole.admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student access required")
    return current_user


async def require_counselor(current_user: models.User = Depends(get_current_user)) -> models.User:
    if current_user.role not in (models.UserRole.counselor, models.UserRole.admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Counselor access required")
    return current_user
