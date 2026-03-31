from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from database.connection import Base


class Session(Base):
    __tablename__ = "sessions"

    session_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"))

    mode = Column(String, nullable=False)  # training / workout

    started_at = Column(TIMESTAMP, server_default=func.now())
    ended_at = Column(TIMESTAMP)