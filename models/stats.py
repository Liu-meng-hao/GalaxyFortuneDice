from sqlalchemy import Column, Integer, DateTime, Date, SmallInteger, Index, UniqueConstraint
from sqlalchemy.sql import func
from config.db_config import Base

class UserHistoryStats(Base):
    __tablename__ = "user_history_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, unique=True)
    total_games = Column(Integer, nullable=False, default=0)
    total_wins = Column(Integer, nullable=False, default=0)
    max_score = Column(Integer, nullable=False, default=0)
    update_time = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class UserDailyStats(Base):
    __tablename__ = "user_daily_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    stat_date = Column(Date, nullable=False, default=func.current_date())
    daily_games = Column(Integer, nullable=False, default=0)
    daily_wins = Column(Integer, nullable=False, default=0)
    daily_max_score = Column(Integer, nullable=False, default=0)
    update_time = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('user_id', 'stat_date', name='uk_user_date'),
    )
