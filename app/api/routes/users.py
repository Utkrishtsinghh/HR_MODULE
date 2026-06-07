import json
import re
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_admin
from app.schemas.user import OnboardingRequest, UserPublic, UserUpdate
from app.db.models import User
from app.db.models import OnboardingDocument
from app.schemas.onboarding import OnboardingDocumentsRequest

from fastapi import UploadFile, File, Form
from pathlib import Path

from app.services.document_verification import (
    verify_pan_document,
    verify_aadhar_document,
)

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
import re

@router.post("/documents")
async def upload_documents(
    aadhar_number: str = Form(...),
    pan_number: str = Form(...),

    aadhar_file: UploadFile = File(...),
    pan_file: UploadFile = File(...),

    marksheet_10_file: UploadFile = File(...),
    marksheet_12_file: UploadFile = File(...),

    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    upload_dir = Path("uploads/documents")
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Save files

    aadhar_path = upload_dir / aadhar_file.filename
    pan_path = upload_dir / pan_file.filename

    marksheet10_path = upload_dir / marksheet_10_file.filename
    marksheet12_path = upload_dir / marksheet_12_file.filename

    with open(aadhar_path, "wb") as f:
        f.write(await aadhar_file.read())

    with open(pan_path, "wb") as f:
        f.write(await pan_file.read())

    with open(marksheet10_path, "wb") as f:
        f.write(await marksheet_10_file.read())

    with open(marksheet12_path, "wb") as f:
        f.write(await marksheet_12_file.read())

    # OCR Verification

    aadhar_result = verify_aadhar_document(
        aadhar_number,
        str(aadhar_path)
    )

    pan_result = verify_pan_document(
        pan_number,
        str(pan_path)
    )

    print("\n========== OCR RESULTS ==========")
    print("AADHAAR:", aadhar_result)
    print("PAN:", pan_result)

    aadhar_valid = aadhar_result.get(
        "verified",
        False
    )

    pan_valid = pan_result.get(
        "verified",
        False
    )

    overall = (
        aadhar_valid
        and
        pan_valid
    )

    return {
        "status": "success",

        "aadhar":
            "Verified"
            if aadhar_valid
            else "Rejected",

        "pan":
            "Verified"
            if pan_valid
            else "Rejected",

        "aadhar_confidence":
            aadhar_result.get(
                "confidence",
                0
            ),

        "pan_confidence":
            pan_result.get(
                "confidence",
                0
            ),

        "extracted_aadhar":
            aadhar_result.get(
                "extracted_aadhar"
            ),

        "extracted_pan":
            pan_result.get(
                "extracted_pan"
            ),

        "overall":
            "Verified"
            if overall
            else "Rejected",
    }

@router.post("/recommendation-letter")
def generate_recommendation_letter(
    current_user=Depends(get_current_user),
):

    return {
        "status": "generated",
        "message": f"Recommendation letter generated for {current_user.full_name}"
    }