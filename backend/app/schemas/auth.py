from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import UserRead


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    full_name: str = Field(min_length=1, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AccessTokenResponse(BaseModel):
    """Returned by /auth/refresh — only a new access token, no new refresh token."""

    access_token: str
    token_type: str = "bearer"


class RegisterResponse(BaseModel):
    user: UserRead
    tokens: TokenResponse


class LoginResponse(BaseModel):
    user: UserRead
    tokens: TokenResponse