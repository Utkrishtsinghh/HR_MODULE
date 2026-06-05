from typing import Optional

from pydantic import BaseModel, EmailStr


class UserPublic(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    role: str
    is_active: bool
    is_onboarded: bool

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    full_name: Optional[str] = None


class OnboardingRequest(BaseModel):
    organization: Optional[str] = None
    notes: Optional[str] = None
