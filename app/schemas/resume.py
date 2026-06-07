from pydantic import BaseModel


class ResumePublic(BaseModel):
    id: int
    job_id: int
    file_name: str

    candidate_email: str | None = None

    score: int
    status: str

    class Config:
        from_attributes = True