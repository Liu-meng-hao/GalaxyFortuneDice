from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from schemas.user import UserResponse

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

    model_config = {"from_attributes": True}
