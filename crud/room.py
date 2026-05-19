from sqlalchemy.orm import Session
from models.room import Room
import random
from typing import List, Optional

def create_room(db: Session, game_mode: int, max_players: int, creator_id: int) -> Room:
    # 房间号ID
    room_id = generate_room_id(db)
    db_room = Room(
        room_id=room_id,
        game_mode=game_mode,
        max_players=max_players,
        creator_id=creator_id
    )
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room

def get_room_by_id(db: Session, room_id: int) -> Optional[Room]:
    return db.query(Room).filter(Room.room_id == room_id).first()

def get_all_rooms(db: Session) -> List[Room]:
    return db.query(Room).filter(Room.status == "waiting").all()


# 生成房间ID(随机房间号)
def generate_room_id(db: Session) -> int:
    while True:
        room_id = random.randint(100000, 999999)
        # 检查是否已存在（假设你有检查房间的函数）
        if not get_room_by_id(db, room_id):
            return room_id