from pydantic import BaseModel, Field
from typing import Optional, List
from schemas.user import UserResponse

class RoomCreate(BaseModel):
    game_mode: str
    max_players: int
    user_id: int

class RoomJoin(BaseModel):
    room_id: str
    user_id: int

class RoomLeave(BaseModel):
    room_id: str
    user_id: int

class RoomResponse(BaseModel):
    room_id: str
    game_mode: str
    max_players: int
    owner_id: int
    status: str
    players: List[UserResponse] = []

class RoomIdResponse(BaseModel):
    room_id: str

class PlayerReady(BaseModel):
    room_id: str
    user_id: int
    ready_status: bool

class PlayersReadyResponse(BaseModel):
    players_ready: dict
