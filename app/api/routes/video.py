from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.emailer import send_email
from app.db.models import Job, VideoInvite, Resume
from app.schemas.video import VideoInviteRequest
from app.services.calendar import generate_meet_link

router = APIRouter(prefix="", tags=["video"])


def _get_job_for_user(db: Session, job_id: int, current_user):
    job = (
        db.query(Job)
        .filter(Job.id == job_id, Job.is_deleted.is_(False))
        .first()
    )

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

    meet_link = payload.meet_link or generate_meet_link()

    invite = VideoInvite(
        job_id=job_id,
        candidate_email=payload.candidate_email,
        meet_link=meet_link,
        scheduled_at=payload.scheduled_at,
        created_by=current_user.id,
    )

    db.add(invite)
    db.commit()

    body = f"""
Dear Candidate,

Congratulations!

You have been shortlisted for the position of {job.title}.

Interview Date & Time:
{payload.scheduled_at}

Google Meet Link:
{meet_link}

If this slot does not work for you, please reply with one of these preferred slots:

• Monday (1 PM – 5 PM IST)
• Wednesday (1 PM – 5 PM IST)
• Saturday (1 PM – 5 PM IST)

Regards,
UTK AI HR Team
"""

    send_email(
        payload.candidate_email,
        "Interview Invitation",
        body,
    )

    return {
        "status": "sent",
        "email": payload.candidate_email,
        "meet_link": meet_link,
    }

@router.post("/jobs/{job_id}/send-shortlist-mails")
def send_shortlist_mails(
    job_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    job = _get_job_for_user(db, job_id, current_user)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    resumes = (
        db.query(Resume)
        .filter(
            Resume.job_id == job_id,
            Resume.score >= 5
        )
        .all()
    )

    sent = 0

    for resume in resumes:

        if not resume.candidate_email:
            continue

        meet_link = generate_meet_link()

        invite = VideoInvite(
            job_id=job_id,
            candidate_email=resume.candidate_email,
            meet_link=meet_link,
            created_by=current_user.id,
        )

        db.add(invite)

        body = f"""
Congratulations!

You have been shortlisted for the position:

{job.title}

Interview Link:
{meet_link}

Please join at the scheduled time.

Regards,
UTK AI HR Team
"""

        try:
            send_email(
                resume.candidate_email,
                "Congratulations! You Are Shortlisted",
                body,
            )
            sent += 1

        except Exception as e:
            print(
                f"Failed sending mail to "
                f"{resume.candidate_email}: {e}"
            )

    db.commit()

    return {
        "status": "success",
        "emails_sent": sent,
        "total_candidates": len(resumes),
    }