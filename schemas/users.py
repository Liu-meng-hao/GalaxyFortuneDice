from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    phone: Optional[str] = None
    nickname: Optional[str] = None

class UserCreate(UserBase):
    password: Optional[str] = None
    is_guest: bool = False

class UserLogin(BaseModel):
    phone: str
    password: str

class UserResponse(UserBase):
    id: int
    avatar: Optional[str] = None
    is_guest: bool
    total_score: int
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class AuthResponse(BaseModel):
    user_info: UserResponse
    token: str

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

class PlayerReady(BaseModel):
    room_id: str
    user_id: int
    ready_status: bool

class MatchStart(BaseModel):
    room_id: str

class MatchState(BaseModel):
    match_id: str
    current_round: int
    current_turn_user: Optional[UserResponse] = None
    phase: str
    selectable_scores: List[str] = []

class RollDice(BaseModel):
    match_id: str
    user_id: int
    lock_mask: Optional[List[bool]] = None

class RollDiceResponse(BaseModel):
    dice_values: List[int]
    remain_throw_count: int

class SelectScore(BaseModel):
    match_id: str
    user_id: int
    score_type: str

class SelectScoreResponse(BaseModel):
    round_score: int
    total_score: int

class GameRecordResponse(BaseModel):
    id: int
    match_id: str
    user_id: int
    round: int
    score_type: str
    round_score: int
    total_score: int
    created_at: datetime

    class Config:
        from_attributes = True

class RankingItem(BaseModel):
    user_id: int
    nickname: str
    avatar: Optional[str] = None
    score: int

class RankingResponse(BaseModel):
    rankings: List[RankingItem]

class MessageResponse(BaseModel):
    message: str

class RoomIdResponse(BaseModel):
    room_id: str

class PlayersReadyResponse(BaseModel):
    players_ready: dict
