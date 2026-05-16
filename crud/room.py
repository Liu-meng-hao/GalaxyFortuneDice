from sqlalchemy.orm import Session
from models.room import Room
import uuid
from typing import List, Optional

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
