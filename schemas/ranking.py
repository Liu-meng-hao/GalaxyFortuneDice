from pydantic import BaseModel, Field
from typing import Optional, List

class RankingItem(BaseModel):
    user_id: int
    nickname: str
    avatar: Optional[str] = None
    rank: int
    total_games: int = 0
    wins: int = 0
    max_score: int = 0

class RankingResponse(BaseModel):
    rankings: List[RankingItem]
    page: int = 1
    page_size: int = 10
    date: Optional[str] = None
    sort_by: Optional[str] = "max_score"
