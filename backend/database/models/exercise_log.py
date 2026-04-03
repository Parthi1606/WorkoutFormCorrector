from sqlalchemy import Column, Integer, Float, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from database.connection import Base


class ExerciseLog(Base):
    __tablename__ = "exercise_logs"

    log_id = Column(Integer, primary_key=True, index=True)

    session_id = Column(Integer, ForeignKey("sessions.session_id", ondelete="CASCADE"))
    exercise_id = Column(Integer, ForeignKey("exercises.exercise_id"))

    reps = Column(Integer, default=0)
    accuracy = Column(Float)
    duration = Column(Integer)

    started_at = Column(TIMESTAMP)
    ended_at = Column(TIMESTAMP)

    created_at = Column(TIMESTAMP, server_default=func.now())