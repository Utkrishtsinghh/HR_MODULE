import json
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.db.models import Job, Resume
from app.schemas.resume import ResumePublic
from app.services.resume_parser import (
    parse_resume,
    extract_email,
)
from app.services.screening import matched_to_json, score_resume
from app.utils.file import save_upload_file

router = APIRouter(prefix="", tags=["resumes"])


def _get_job_for_user(db: Session, job_id: int, current_user):
    job = db.query(Job).filter(Job.id == job_id, Job.is_deleted.is_(False)).first()
    if not job:
        return None
    if current_user.role != "admin" and job.created_by != current_user.id:
        return None
    return job


@router.post("/jobs/{job_id}/resumes/bulk", response_model=list[ResumePublic])
def upload_resumes(
    job_id: int,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    job = _get_job_for_user(db, job_id, current_user)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    uploads_dir = Path("uploads") / str(job_id)
    uploads_dir.mkdir(parents=True, exist_ok=True)

    results = []

    for upload in files:

        dest = uploads_dir / upload.filename

        save_upload_file(upload, dest)

        text = parse_resume(str(dest))

        email = extract_email(text)

        print("================================")
        print("FILE:", upload.filename)
        print("EMAIL FOUND:", email)
        print("================================")

        tags = json.loads(job.tags_json or "[]")
        
        score, matched = score_resume(
            tags,
            text
        )
        
        resume = Resume(
            job_id=job_id,
            file_name=upload.filename,
            file_path=str(dest),
            text=text,
            candidate_email=email,
            score=score,
            matched_tags_json=matched_to_json(matched),
            status="scored",
        )

        db.add(resume)
        db.commit()
        db.refresh(resume)

        results.append(resume)

    return results


@router.get("/jobs/{job_id}/resumes", response_model=list[ResumePublic])
def list_resumes(job_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    job = _get_job_for_user(db, job_id, current_user)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return db.query(Resume).filter(Resume.job_id == job_id).all()


@router.get("/resumes/{resume_id}")
def resume_detail(resume_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    job = _get_job_for_user(db, resume.job_id, current_user)
    if not job:
        raise HTTPException(status_code=404, detail="Not allowed")
    return {
    "id": resume.id,
    "job_id": resume.job_id,
    "file_name": resume.file_name,
    "candidate_email": resume.candidate_email,
    "score": resume.score,
    "status": resume.status,
    "matched_tags": json.loads(resume.matched_tags_json or "[]"),}

@router.post("/jobs/{job_id}/screen")
def screen_resumes(job_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    job = _get_job_for_user(db, job_id, current_user)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    tags = json.loads(job.tags_json or "[]")
    resumes = db.query(Resume).filter(Resume.job_id == job_id).all()

    for resume in resumes:
        score, matched = score_resume(tags, resume.text or "")
        resume.score = score
        resume.matched_tags_json = matched_to_json(matched)
        resume.status = "scored"
    db.commit()

    return {"status": "scored", "count": len(resumes)}
