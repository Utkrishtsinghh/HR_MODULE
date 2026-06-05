from pydantic import BaseModel


class ResumePublic(BaseModel):
    id: int
    job_id: int
    file_name: str
    score: int
    status: str

    class Config:
        from_attributes = True
