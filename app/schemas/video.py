from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr

class VideoInviteRequest(BaseModel):
    candidate_email: EmailStr
    scheduled_at: datetime | None = None
    meet_link: str | None = None  