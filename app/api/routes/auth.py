from datetime import datetime, timedelta
import json
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.core.emailer import send_email
from app.core.security import create_access_token, hash_password, try_decode_token, verify_password
from app.db.models import Invite, Token, User
from app.schemas.auth import InviteRequest, LoginRequest, SignupRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


def _get_optional_user(request: Request, db: Session) -> Optional[User]:
    auth = request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        return None
    token = auth.split(" ", 1)[1]
    payload = try_decode_token(token)
    if not payload:
        return None
    jti = payload.get("jti")
    user_id = payload.get("sub")
    if not jti or not user_id:
        return None
    token_row = db.query(Token).filter(Token.jti == jti, Token.revoked.is_(False)).first()
    if not token_row:
        return None
    return db.query(User).filter(User.id == int(user_id), User.is_active.is_(True)).first()


@router.post("/invite")
def invite_user(payload: InviteRequest, request: Request, db: Session = Depends(get_db)):
    existing_users = db.query(User).count()
    current_user = _get_optional_user(request, db)
    if existing_users > 0:
        if not current_user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login required")
        if current_user.role != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")

    token = uuid.uuid4().hex
    expires_at = datetime.utcnow() + timedelta(days=payload.expires_in_days)
    invite = Invite(
        email=payload.email,
        token=token,
        invited_by=current_user.id if current_user else None,
        expires_at=expires_at,
    )
    db.add(invite)
    db.commit()

    signup_link = f"{settings.frontend_base_url}/signup.html?token={token}&email={payload.email}"
    body = f"You are invited to signup. Use this link: {signup_link}"
    send_email(payload.email, "Signup Invite", body)

    return {"invite_token": token, "signup_link": signup_link}


@router.post("/signup", response_model=TokenResponse)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    invite = db.query(Invite).filter(Invite.token == payload.invite_token).first()
    if not invite or invite.used_at:
        raise HTTPException(status_code=400, detail="Invalid invite token")
    if invite.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invite expired")
    if invite.email.lower() != payload.email.lower():
        raise HTTPException(status_code=400, detail="Email mismatch")

    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role="admin" if db.query(User).count() == 0 else "user",
    )
    db.add(user)
    invite.used_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    token, jti, exp = create_access_token(str(user.id))
    token_row = Token(jti=jti, user_id=user.id, expires_at=exp)
    db.add(token_row)
    db.commit()

    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token, jti, exp = create_access_token(str(user.id))
    token_row = Token(jti=jti, user_id=user.id, expires_at=exp)
    db.add(token_row)
    db.commit()

    return TokenResponse(access_token=token)


@router.post("/logout")
def logout(request: Request, db: Session = Depends(get_db)):
    auth = request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing token")

    token = auth.split(" ", 1)[1]
    payload = try_decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    jti = payload.get("jti")
    token_row = db.query(Token).filter(Token.jti == jti, Token.revoked.is_(False)).first()
    if token_row:
        token_row.revoked = True
        db.commit()

    return {"status": "logged_out"}


@router.post("/refresh", response_model=TokenResponse)
def refresh(request: Request, db: Session = Depends(get_db)):
    auth = request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing token")

    token = auth.split(" ", 1)[1]
    payload = try_decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    jti = payload.get("jti")
    user_id = payload.get("sub")
    token_row = db.query(Token).filter(Token.jti == jti, Token.revoked.is_(False)).first()
    if not token_row:
        raise HTTPException(status_code=401, detail="Token revoked")

    token_row.revoked = True
    new_token, new_jti, exp = create_access_token(str(user_id))
    db.add(Token(jti=new_jti, user_id=int(user_id), expires_at=exp))
    db.commit()

    return TokenResponse(access_token=new_token)
