from pydantic import BaseModel, EmailStr, ConfigDict
from src.auth.models import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: UserRole = UserRole.student


class UserResponse(BaseModel):
    id: int
    email: str
    role: UserRole
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenData(BaseModel):
    user_id: int | None = None
    role: str | None = None
