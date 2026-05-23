from sqlalchemy import Column, Integer, String, DateTime, SmallInteger
from sqlalchemy.sql import func
from config.db_config import Base

class Room(Base):
    __tablename__ = "t_room"

    room_id = Column(Integer, primary_key=True, autoincrement=True)
    game_mode = Column(SmallInteger, nullable=False, default=1)
    creator_id = Column(Integer, nullable=False, index=True)
    room_status = Column(SmallInteger, nullable=False, default=1)
    max_players = Column(SmallInteger, nullable=False, default=2)
    current_players = Column(SmallInteger, nullable=False, default=0)
    create_time = Column(DateTime(timezone=True), server_default=func.now())
    expire_time = Column(DateTime(timezone=True), nullable=True)