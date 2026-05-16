from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text
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

class Room(Base):
    __tablename__ = "t_rooms"

    id = Column(Integer, primary_key=True, autoincrement=True)
    room_id = Column(String(50), unique=True, index=True)
    game_mode = Column(String(20))
    max_players = Column(Integer)
    owner_id = Column(Integer)
    status = Column(String(20), default="waiting")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

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
