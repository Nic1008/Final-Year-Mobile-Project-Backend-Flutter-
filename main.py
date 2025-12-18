from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime, timedelta, date, time
from typing import Dict, List

from sqlalchemy.orm import Session
from sqlalchemy import func

from database import Base, engine, SessionLocal
from models import User, WorkoutLog
from routes import auth
from pydantic import BaseModel


# ======================================================
# App
# ======================================================
app = FastAPI(title="Fitness App API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)
app.include_router(auth.router)

class ProfileUpdate(BaseModel):
    email: str
    display_name: str | None = None
    age: int
    weight: float
    height: float
    gender: str | None = None
    target_weight: float
    avatar_url: str | None = None


# ======================================================
# DB Dependency
# ======================================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ======================================================
# Helpers
# ======================================================
def start_of_week_utc():
    today = datetime.utcnow().date()
    monday = today - timedelta(days=today.weekday())
    return datetime.combine(monday, time.min)


def default_progress():
    return {
        "weekly_steps": [0, 0, 0, 0, 0, 0, 0],
        "daily_steps": 0,
        "total_runs": 0,
        "best_run_km": 0.0,
    }


# ======================================================
# LEGACY in-memory cardio (Flutter still uses this)
# ======================================================
user_progress: Dict[str, Dict] = {}


# ======================================================
# Routes
# ======================================================
@app.get("/")
def root():
    return {"message": "Fitness App Backend Running!"}


# ---------------- PROFILE ----------------
@app.get("/profile")
def get_profile(email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "name": user.display_name or user.name,  
        "email": user.email,
        "age": user.age,
        "weight": user.weight,
        "height": user.height,
        "gender": user.gender,
        "target_weight": user.target_weight,
        "avatar_url": user.avatar_url,
    }
    
@app.put("/profile")
def update_profile(payload: ProfileUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if payload.display_name is not None:
      user.display_name = payload.display_name


    user.age = payload.age
    user.weight = payload.weight
    user.height = payload.height
    user.gender = payload.gender
    user.target_weight = payload.target_weight
    user.avatar_url = payload.avatar_url

    db.commit()

    return {"message": "Profile updated successfully"}


# ---------------- PROGRESS (CARDIO – LEGACY) ----------------
@app.get("/progress")
def get_progress(email: str):
    if email not in user_progress:
        user_progress[email] = default_progress()
    return user_progress[email]


# ---------------- WEEKLY SUMMARY ----------------
@app.get("/progress/weekly-summary")
def weekly_summary(email: str, db: Session = Depends(get_db)):
    week_start = start_of_week_utc()
    week_end = week_start + timedelta(days=7)

    weekly_count = db.query(
        func.count(func.distinct(func.date(WorkoutLog.logged_at)))
    ).filter(
        WorkoutLog.email == email,
        WorkoutLog.logged_at >= week_start,
        WorkoutLog.logged_at < week_end
    ).scalar() or 0

    return {
        "weekly_workouts": weekly_count,
        "weekly_goal": 5
    }


# ---------------- DAILY CHECKINS ----------------
@app.get("/progress/daily-checkins")
def daily_checkins(email: str, db: Session = Depends(get_db)):
    week_start = start_of_week_utc()
    week_end = week_start + timedelta(days=7)

    logs = db.query(WorkoutLog).filter(
        WorkoutLog.email == email,
        WorkoutLog.logged_at >= week_start,
        WorkoutLog.logged_at < week_end
    ).all()

    result = {
        "mon": False,
        "tue": False,
        "wed": False,
        "thu": False,
        "fri": False,
        "sat": False,
        "sun": False,
    }

    for log in logs:
        day = log.logged_at.strftime("%a").lower()[:3]
        if day in result:
            result[day] = True

    return result

@app.post("/progress/workout/checkin")
def log_workout(email: str, db: Session = Depends(get_db)):
    today = date.today()

    # Prevent duplicate check-in for the same day
    exists = db.query(WorkoutLog).filter(
        WorkoutLog.email == email,
        func.date(WorkoutLog.logged_at) == today
    ).first()

    if exists:
        raise HTTPException(status_code=400, detail="Workout already logged today")

    log = WorkoutLog(email=email)
    db.add(log)
    db.commit()

    return {"message": "Workout logged successfully"}


# ======================================================
# Run
# ======================================================
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)

