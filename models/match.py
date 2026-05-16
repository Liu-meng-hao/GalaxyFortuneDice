from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from config.db_config import Base

class Match(Base):
    __tablename__ = "t_matches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(String(50), unique=True, index=True)
    room_id = Column(String(50), index=True)
    current_round = Column(Integer, default=1)
    current_turn_user_id = Column(Integer)
    phase = Column(String(20), default="rolling")
    status = Column(String(20), default="ongoing")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)

class GameRecord(Base):
    __tablename__ = "t_game_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(String(50), index=True)
    user_id = Column(Integer, index=True)
    round = Column(Integer)
    score_type = Column(String(50))
    round_score = Column(Integer)
    total_score = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
