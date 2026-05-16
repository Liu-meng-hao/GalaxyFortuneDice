from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from config.db_config import Base

class Room(Base):
    __tablename__ = "t_rooms"

    id = Column(Integer, primary_key=True, autoincrement=True)
    room_id = Column(String(50), unique=True, index=True)
    game_mode = Column(String(20))
    max_players = Column(Integer)
    owner_id = Column(Integer)
    status = Column(String(20), default="waiting")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
