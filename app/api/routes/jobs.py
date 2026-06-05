from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.db.models import Job
from app.schemas.job import JobCreate, JobPublic, JobUpdate
from app.services.gemini import generate_tags
from app.services.screening import tags_to_json

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _get_job_for_user(db: Session, job_id: int, current_user):
    job = db.query(Job).filter(Job.id == job_id, Job.is_deleted.is_(False)).first()
    if not job:
        return None
    if current_user.role != "admin" and job.created_by != current_user.id:
        return None
    return job


@router.post("", response_model=JobPublic)
def create_job(payload: JobCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    tags = generate_tags(payload.jd_text)
    job = Job(
        title=payload.title,
        jd_text=payload.jd_text,
        tags_json=tags_to_json(tags),
        created_by=current_user.id,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.get("", response_model=list[JobPublic])
def list_jobs(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.role == "admin":
        return db.query(Job).filter(Job.is_deleted.is_(False)).all()
    return db.query(Job).filter(Job.created_by == current_user.id, Job.is_deleted.is_(False)).all()


@router.get("/{job_id}", response_model=JobPublic)
def get_job(job_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    job = _get_job_for_user(db, job_id, current_user)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.patch("/{job_id}", response_model=JobPublic)
def update_job(job_id: int, payload: JobUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    job = _get_job_for_user(db, job_id, current_user)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if payload.title is not None:
        job.title = payload.title
    if payload.jd_text is not None:
        job.jd_text = payload.jd_text
        tags = generate_tags(payload.jd_text)
        job.tags_json = tags_to_json(tags)
    db.commit()
    db.refresh(job)
    return job


@router.delete("/{job_id}")
def delete_job(job_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    job = _get_job_for_user(db, job_id, current_user)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.is_deleted = True
    db.commit()
    return {"status": "deleted"}
