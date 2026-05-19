from sqlalchemy import Column, Integer, String, DateTime, SmallInteger, Index
from sqlalchemy.sql import func
from config.db_config import Base

class Match(Base):
    __tablename__ = "t_match"

    id = Column(Integer, primary_key=True, autoincrement=True)
    room_id = Column(Integer, nullable=False, index=True)
    game_mode = Column(SmallInteger, nullable=False, default=1)
    total_round = Column(Integer, nullable=False, default=13)
    match_status = Column(SmallInteger, nullable=False, default=1)
    winner_user_id = Column(Integer, nullable=True)
    winner_team_id = Column(SmallInteger, nullable=True)
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)

class MatchScoreSheet(Base):
    __tablename__ = "t_match_score_sheet"

    id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False)
    score_type = Column(String(32), nullable=False)
    score = Column(Integer, nullable=False, default=0)
    create_time = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('uk_match_user_score', 'match_id', 'user_id', 'score_type', unique=True),
    )

class GameRecord(Base):
    __tablename__ = "t_game_record"

    id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    final_score = Column(Integer, nullable=False, default=0)
    rank = Column(SmallInteger, nullable=False, default=0)
    is_win = Column(SmallInteger, nullable=False, default=0)
    game_mode = Column(SmallInteger, nullable=False, default=1)
    duration = Column(Integer, nullable=True)
    create_time = Column(DateTime(timezone=True), server_default=func.now())
