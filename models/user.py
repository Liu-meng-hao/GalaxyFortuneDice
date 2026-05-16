from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from config.db_config import Base

class User(Base):
    __tablename__ = "t_users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phone = Column(String(20), unique=True, index=True)
    nickname = Column(String(50))
    password_hash = Column(String(255))
    avatar = Column(String(255), nullable=True)
    is_guest = Column(Boolean, default=False)
    total_score = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
