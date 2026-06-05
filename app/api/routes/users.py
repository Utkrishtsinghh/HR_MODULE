import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_admin
from app.schemas.user import OnboardingRequest, UserPublic, UserUpdate
from app.db.models import User

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserPublic)
def get_me(current_user=Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserPublic)
def update_me(payload: UserUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if payload.full_name is not None:
        current_user.full_name = payload.full_name
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/onboarding")
def user_onboarding(payload: OnboardingRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    current_user.onboarding_json = json.dumps(payload.model_dump(), ensure_ascii=True)
    current_user.is_onboarded = True
    db.commit()
    return {"status": "onboarded"}


@router.get("/onboarded", response_model=list[UserPublic])
def onboarded_users(db: Session = Depends(get_db), current_user=Depends(require_admin)):
    users = db.query(User).filter(User.is_onboarded.is_(True)).all()
    return users
