from typing import Optional

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class InviteRequest(BaseModel):
    email: EmailStr
    expires_in_days: int = 7


class SignupRequest(BaseModel):
    invite_token: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
