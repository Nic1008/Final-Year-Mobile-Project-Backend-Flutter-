from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import SessionLocal
from models import User, WorkoutLog
from auth_utils import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Auth"])


# ---------------- DB Dependency ----------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------- Schemas ----------------
class SignupPayload(BaseModel):
    name: str
    email: str
    password: str


class LoginPayload(BaseModel):
    email: str
    password: str


class DeleteAccountRequest(BaseModel):
    email: str


# ---------------- Routes ----------------
@router.post("/register")
def register(payload: SignupPayload, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    user = User(
        name=payload.name,
        display_name=payload.name,   # ✅ INIT PROFILE
        email=payload.email,
        hashed_password=hash_password(payload.password),
        age=None,
        weight=None,
        height=None,
        gender=None,
        target_weight=None,
        avatar_url=None,
    )

    db.add(user)
    db.commit()

    return {"message": "Signup successful"}


@router.post("/login")
def login(payload: LoginPayload, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(user.email)

    return {
        "message": "Login successful",
        "token": token,
        "profile": {
            "display_name": user.display_name,
            "email": user.email
        }
    }


@router.delete("/delete-account")
def delete_account(req: DeleteAccountRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.query(WorkoutLog).filter(WorkoutLog.email == req.email).delete()
    db.delete(user)
    db.commit()

    return {"message": "Account deleted successfully"}

