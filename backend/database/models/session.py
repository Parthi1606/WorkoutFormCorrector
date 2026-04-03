"""
database/models/session.py
---------------------------
One row per completed exercise session.
Named SessionModel to avoid collision with FastAPI's Session type.
"""
from sqlalchemy import Column, Integer, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from database.connection import Base


class SessionModel(Base):
    __tablename__ = "sessions"

    session_id = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    started_at = Column(TIMESTAMP, nullable=False)
    ended_at   = Column(TIMESTAMP, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
