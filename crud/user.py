from sqlalchemy.orm import Session
from models.user import User
from schemas.user import UserCreate
from utils.security import get_password_hash
import uuid
from typing import Optional

def get_user_by_phone(db: Session, phone: str) -> Optional[User]:
    return db.query(User).filter(User.phone == phone).first()

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()

def create_user(db: Session, user: UserCreate) -> User:
    hashed_password = None
    if user.password:
        hashed_password = get_password_hash(user.password)
    db_user = User(
        phone=user.phone,
        nickname=user.nickname,
        password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_guest_user(db: Session) -> User:
    guest_nickname = f"游客_{uuid.uuid4().hex[:8]}"
    db_user = User(
        nickname=guest_nickname
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user_total_score(db: Session, user_id: int, score: int):
    user = get_user_by_id(db, user_id)
    if user:
        user.exp += score
        db.commit()
