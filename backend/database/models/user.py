from sqlalchemy import Column, Integer, Text, TIMESTAMP
from sqlalchemy.sql import func
from database.connection import Base

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    email = Column(Text, unique=True, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())