from fastapi import APIRouter, Depends
from typing import Optional
from datetime import datetime
from config.db_config import get_redis
from schemas.ranking import RankingResponse, RankingItem
from crud.redis_manager import RedisManager

router = APIRouter(prefix="/api/ranking", tags=["排行榜"])

@router.get("/total", response_model=RankingResponse)
async def get_total_ranking(limit: int = 10, redis = Depends(get_redis)):
    redis_manager = RedisManager(redis)
    rankings_data = redis_manager.get_total_ranking(limit)
    
    rankings = []
    for member, score in rankings_data:
        parts = member.split(":", 1)
        user_id = int(parts[0])
        nickname = parts[1] if len(parts) > 1 else ""
        rankings.append(RankingItem(
            user_id=user_id,
            nickname=nickname,
            avatar=None,
            score=int(score)
        ))
    
    return RankingResponse(rankings=rankings)

@router.get("/daily", response_model=RankingResponse)
async def get_daily_ranking(date: Optional[str] = None, limit: int = 10, redis = Depends(get_redis)):
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    
    redis_manager = RedisManager(redis)
    rankings_data = redis_manager.get_daily_ranking(date, limit)
    
    rankings = []
    for member, score in rankings_data:
        parts = member.split(":", 1)
        user_id = int(parts[0])
        nickname = parts[1] if len(parts) > 1 else ""
        rankings.append(RankingItem(
            user_id=user_id,
            nickname=nickname,
            avatar=None,
            score=int(score)
        ))
    
    return RankingResponse(rankings=rankings)
