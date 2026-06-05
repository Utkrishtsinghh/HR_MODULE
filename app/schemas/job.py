from typing import Optional

from pydantic import BaseModel


class JobCreate(BaseModel):
    title: str
    jd_text: str


class JobUpdate(BaseModel):
    title: Optional[str] = None
    jd_text: Optional[str] = None


class JobPublic(BaseModel):
    id: int
    title: str
    jd_text: str
    tags_json: Optional[str] = None
    created_by: int
    is_deleted: bool

    class Config:
        from_attributes = True
