"""
database/models/exercise.py
----------------------------
Static lookup table — one row per supported exercise.
Seeded once via seed_exercises() below.
"""
from sqlalchemy import Column, Integer, Text, Boolean
from database.connection import Base


class Exercise(Base):
    __tablename__ = "exercises"

    exercise_id  = Column(Integer, primary_key=True, index=True)
    exercise_key = Column(Text, unique=True, nullable=False)  # matches EXERCISE_REGISTRY keys
    name         = Column(Text, nullable=False)               # display name
    is_hold      = Column(Boolean, default=False)             # True for plank


# ── Seed data ─────────────────────────────────────────────────────────────────
# Call this once after creating tables:
#   from database.models.exercise import seed_exercises
#   seed_exercises(db)

EXERCISE_SEED = [
    {"exercise_key": "bicep_curl",     "name": "Bicep Curl",      "is_hold": False},
    {"exercise_key": "squat",          "name": "Squat",           "is_hold": False},
    {"exercise_key": "shoulder_press", "name": "Shoulder Press",  "is_hold": False},
    {"exercise_key": "lunge",          "name": "Lunge",           "is_hold": False},
    {"exercise_key": "pushup",         "name": "Push-up",         "is_hold": False},
    {"exercise_key": "bent_over_row",  "name": "Bent-Over Row",   "is_hold": False},
    {"exercise_key": "plank",          "name": "Plank",           "is_hold": True},
]


def seed_exercises(db):
    from database.models.exercise import Exercise
    for data in EXERCISE_SEED:
        exists = db.query(Exercise).filter(
            Exercise.exercise_key == data["exercise_key"]
        ).first()
        if not exists:
            db.add(Exercise(**data))
    db.commit()
    print("Exercises seeded.")
