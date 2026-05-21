from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from schemas.user import UserResponse

class MatchStart(BaseModel):
    room_id: int

class MatchUserInfo(BaseModel):
    user_id: int
    nickname: str
    team_id: int
    seat_no: int 
    ready_status: bool ######
    is_online: bool  ######

class MatchStartResponse(BaseModel):
    id: int
    match_info: List[MatchUserInfo]

class SelectableScore(BaseModel):
    type: str
    score: int

class MatchState(BaseModel):
    match_id: int
    room_id: int
    current_round: int
    current_turn_user_id: int
    current_seat_no: int
    phase: str
    remain_throw_count: int
    dice_values: List[int] = []
    locked_dice: List[int] = []
    selectable_scores: List[SelectableScore] = []

class RollDice(BaseModel):
    match_id: int
    user_id: int
    lock_mask: List[int]

class RollDiceResponse(BaseModel):
    dice_values: List[int]
    remain_throw_count: int

class SelectScore(BaseModel):
    match_id: int
    user_id: int
    score_type: str

class SelectScoreResponse(BaseModel):
    round_score: int
    total_score: int
