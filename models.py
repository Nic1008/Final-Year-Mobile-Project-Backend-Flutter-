from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime

from database import Base   # ✅ THIS LINE WAS MISSING


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    # Account / signup name (internal)
    name = Column(String, nullable=True)

    # Preferred name from onboarding (UI-facing)
    display_name = Column(String, nullable=True) 
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    age = Column(Integer, nullable=True)
    gender = Column(String, nullable=True)

    height = Column(Float, nullable=True)
    weight = Column(Float, nullable=True)
    target_weight = Column(Float, nullable=True)

    avatar_url = Column(String, nullable=True)


# ======================
# Workout log model
# ======================
class WorkoutLog(Base):
    __tablename__ = "workout_logs"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True, nullable=False)
    logged_at = Column(DateTime, default=datetime.utcnow)


