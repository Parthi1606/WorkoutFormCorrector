"""
init_db.py
----------
Run once to create all tables and seed the exercises lookup table.

Usage:
    cd backend
    python init_db.py
"""
from database.connection import engine, SessionLocal, Base

# Import all models so Base knows about them before create_all
from database.models.user import User
from database.models.session import SessionModel
from database.models.exercise import Exercise, seed_exercises
from database.models.exercise_log import ExerciseLog
from database.models.user_stats import UserStats

def init():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created.")

    db = SessionLocal()
    try:
        seed_exercises(db)
    finally:
        db.close()

    print("Database ready.")

if __name__ == "__main__":
    init()
