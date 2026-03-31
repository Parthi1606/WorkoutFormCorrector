from sqlalchemy import Column, Integer, Float, ForeignKey, TIMESTAMP, UniqueConstraint
from sqlalchemy.sql import func
from database.connection import Base


class UserStats(Base):
    __tablename__ = "user_stats"

    stat_id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"))
    exercise_id = Column(Integer, ForeignKey("exercises.exercise_id"))

    total_reps = Column(Integer, default=0)
    total_sessions = Column(Integer, default=0)
    avg_accuracy = Column(Float, default=0)

    last_updated = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "exercise_id", name="unique_user_exercise"),
    )