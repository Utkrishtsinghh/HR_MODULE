from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.emailer import send_email
from app.db.models import Job, VideoInvite
from app.schemas.video import VideoInviteRequest
from app.services.calendar import generate_meet_link

router = APIRouter(prefix="", tags=["video"])


def _get_job_for_user(db: Session, job_id: int, current_user):
    job = db.query(Job).filter(Job.id == job_id, Job.is_deleted.is_(False)).first()
    if not job:
        return None
    if current_user.role != "admin" and job.created_by != current_user.id:
        return None
    return job


@router.post("/jobs/{job_id}/video-invite")
def create_video_invite(
    job_id: int,
    payload: VideoInviteRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    job = _get_job_for_user(db, job_id, current_user)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    meet_link = generate_meet_link()
    invite = VideoInvite(
        job_id=job_id,
        candidate_email=payload.candidate_email,
        meet_link=meet_link,
        scheduled_at=payload.scheduled_at,
        created_by=current_user.id,
    )
    db.add(invite)
    db.commit()

    body = f"Interview invite for {job.title}. Join: {meet_link}"
    send_email(payload.candidate_email, "Video Interview Invite", body)

    return {"status": "sent", "meet_link": meet_link}
