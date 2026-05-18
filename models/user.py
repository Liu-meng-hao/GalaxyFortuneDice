from sqlalchemy import Column, Integer, String, DateTime, SmallInteger, BigInteger
from sqlalchemy.sql import func
from config.db_config import Base


class User(Base):
    __tablename__ = "t_users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    phone = Column(String(64), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    nickname = Column(String(32), unique=True, nullable=False)
    avatar = Column(String(255), nullable=False, default='default_avatar.png')
    exp = Column(BigInteger, nullable=False, default=0)
    status = Column(SmallInteger, nullable=False, default=0)
    create_time = Column(DateTime, nullable=False, server_default=func.now())
    update_time = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
