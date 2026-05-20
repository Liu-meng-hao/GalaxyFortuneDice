from pydantic import BaseModel, Field
from typing import Optional, List

class RoomCreate(BaseModel):
    game_mode: int
    max_players: int
    user_id: int

class RoomJoin(BaseModel):
    room_id: int
    user_id: int

class RoomLeave(BaseModel):
    room_id: int
    user_id: int

class RoomResponse(BaseModel):
    room_id: int
    game_mode: int
    current_players: int = 0
    max_players: int
    creator_id: int
    room_status: int
    players: List[dict] = []


class PlayerReady(BaseModel):
    room_id: int
    user_id: int
    ready_status: bool


