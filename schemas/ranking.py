from pydantic import BaseModel, Field
from typing import Optional, List

class RankingItem(BaseModel):
    user_id: int
    nickname: str
    avatar: Optional[str] = None
    score: int

class RankingResponse(BaseModel):
    rankings: List[RankingItem]
