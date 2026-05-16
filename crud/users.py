from sqlalchemy.orm import Session
from models.users import User, Room, Match, GameRecord
from schemas.users import UserCreate
from utils.security import get_password_hash
import uuid
import json
from typing import List, Optional
from datetime import datetime

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
        password_hash=hashed_password,
        is_guest=user.is_guest
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_guest_user(db: Session) -> User:
    guest_nickname = f"游客_{uuid.uuid4().hex[:8]}"
    db_user = User(
        nickname=guest_nickname,
        is_guest=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_room(db: Session, game_mode: str, max_players: int, owner_id: int) -> Room:
    room_id = f"room_{uuid.uuid4().hex[:8]}"
    db_room = Room(
        room_id=room_id,
        game_mode=game_mode,
        max_players=max_players,
        owner_id=owner_id
    )
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room

def get_room_by_id(db: Session, room_id: str) -> Optional[Room]:
    return db.query(Room).filter(Room.room_id == room_id).first()

def get_all_rooms(db: Session) -> List[Room]:
    return db.query(Room).filter(Room.status == "waiting").all()

def create_match(db: Session, room_id: str) -> Match:
    match_id = f"match_{uuid.uuid4().hex[:8]}"
    db_match = Match(
        match_id=match_id,
        room_id=room_id
    )
    db.add(db_match)
    db.commit()
    db.refresh(db_match)
    return db_match

def get_match_by_id(db: Session, match_id: str) -> Optional[Match]:
    return db.query(Match).filter(Match.match_id == match_id).first()

def create_game_record(
    db: Session,
    match_id: str,
    user_id: int,
    round: int,
    score_type: str,
    round_score: int,
    total_score: int
) -> GameRecord:
    db_record = GameRecord(
        match_id=match_id,
        user_id=user_id,
        round=round,
        score_type=score_type,
        round_score=round_score,
        total_score=total_score
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

def get_game_records_by_match(db: Session, match_id: str) -> List[GameRecord]:
    return db.query(GameRecord).filter(GameRecord.match_id == match_id).all()

def update_user_total_score(db: Session, user_id: int, score: int):
    user = get_user_by_id(db, user_id)
    if user:
        user.total_score += score
        db.commit()

class RedisManager:
    def __init__(self, redis_client):
        self.redis = redis_client

    def set_room_players(self, room_id: str, players: List[dict]):
        key = f"room:{room_id}:players"
        self.redis.set(key, json.dumps(players))

    def get_room_players(self, room_id: str) -> List[dict]:
        key = f"room:{room_id}:players"
        data = self.redis.get(key)
        return json.loads(data) if data else []

    def set_player_ready(self, room_id: str, user_id: int, ready: bool):
        key = f"room:{room_id}:ready"
        self.redis.hset(key, str(user_id), "1" if ready else "0")

    def get_players_ready(self, room_id: str) -> dict:
        key = f"room:{room_id}:ready"
        data = self.redis.hgetall(key)
        return {int(k): v == "1" for k, v in data.items()}

    def set_match_state(self, match_id: str, state: dict):
        key = f"match:{match_id}:state"
        self.redis.set(key, json.dumps(state))

    def get_match_state(self, match_id: str) -> Optional[dict]:
        key = f"match:{match_id}:state"
        data = self.redis.get(key)
        return json.loads(data) if data else None

    def set_dice_state(self, match_id: str, dice_values: List[int], remain_throws: int):
        key = f"match:{match_id}:dice"
        data = {
            "dice_values": dice_values,
            "remain_throws": remain_throws
        }
        self.redis.set(key, json.dumps(data))

    def get_dice_state(self, match_id: str) -> Optional[dict]:
        key = f"match:{match_id}:dice"
        data = self.redis.get(key)
        return json.loads(data) if data else None

    def set_player_scores(self, match_id: str, user_id: int, scores: dict):
        key = f"match:{match_id}:scores:{user_id}"
        self.redis.set(key, json.dumps(scores))

    def get_player_scores(self, match_id: str, user_id: int) -> Optional[dict]:
        key = f"match:{match_id}:scores:{user_id}"
        data = self.redis.get(key)
        return json.loads(data) if data else None

    def update_total_ranking(self, user_id: int, nickname: str, score: int):
        key = "ranking:total"
        member = f"{user_id}:{nickname}"
        self.redis.zadd(key, {member: score})

    def get_total_ranking(self, limit: int) -> List[tuple]:
        key = "ranking:total"
        return self.redis.zrevrange(key, 0, limit - 1, withscores=True)

    def update_daily_ranking(self, date: str, user_id: int, nickname: str, score: int):
        key = f"ranking:daily:{date}"
        member = f"{user_id}:{nickname}"
        self.redis.zadd(key, {member: score})

    def get_daily_ranking(self, date: str, limit: int) -> List[tuple]:
        key = f"ranking:daily:{date}"
        return self.redis.zrevrange(key, 0, limit - 1, withscores=True)
