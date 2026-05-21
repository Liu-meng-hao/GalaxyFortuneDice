from fastapi import APIRouter, Depends
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from config.db_config import get_redis, get_db
from schemas.ranking import RankingResponse, RankingItem
from crud.redis_manager import RedisManager
from crud.user import get_user_by_id
from models.stats import UserHistoryStats, UserDailyStats

router = APIRouter(prefix="/api/ranking", tags=["排行榜"])

@router.get("/total", response_model=RankingResponse)
async def get_total_ranking(limit: int = 10, redis = Depends(get_redis), db: Session = Depends(get_db)):
    redis_manager = RedisManager(redis)
    rankings_data = redis_manager.get_total_ranking(limit)
    
    # 如果Redis中没有数据，从MySQL加载
    if not rankings_data:
        rankings_data = await _load_total_ranking_from_db(db, redis_manager, limit)
    
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
async def get_daily_ranking(date: Optional[str] = None, limit: int = 10, redis = Depends(get_redis), db: Session = Depends(get_db)):
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    
    redis_manager = RedisManager(redis)
    rankings_data = redis_manager.get_daily_ranking(date, limit)
    
    # 如果Redis中没有数据，从MySQL加载
    if not rankings_data:
        rankings_data = await _load_daily_ranking_from_db(db, redis_manager, date, limit)
    
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

async def _load_total_ranking_from_db(db: Session, redis_manager: RedisManager, limit: int):
    """从MySQL加载总排行榜数据到Redis"""
    # 查询历史统计表，按最高分排序
    stats = db.query(UserHistoryStats).order_by(UserHistoryStats.max_score.desc()).limit(limit * 2).all()
    
    for stat in stats:
        # 获取用户昵称
        user = get_user_by_id(db, stat.user_id)
        nickname = user.nickname if user else ""
        # 更新到Redis
        redis_manager.update_total_ranking(stat.user_id, nickname, stat.max_score)
    
    # 重新从Redis获取
    return redis_manager.get_total_ranking(limit)

async def _load_daily_ranking_from_db(db: Session, redis_manager: RedisManager, date: str, limit: int):
    """从MySQL加载日排行榜数据到Redis"""
    from datetime import datetime as dt
    
    # 将字符串日期转换为date对象
    stat_date = dt.strptime(date, "%Y-%m-%d").date()
    
    # 查询每日统计表，按当日最高分排序
    stats = db.query(UserDailyStats).filter(
        UserDailyStats.stat_date == stat_date
    ).order_by(UserDailyStats.daily_max_score.desc()).limit(limit * 2).all()
    
    for stat in stats:
        # 获取用户昵称
        user = get_user_by_id(db, stat.user_id)
        nickname = user.nickname if user else ""
        # 更新到Redis
        redis_manager.update_daily_ranking(date, stat.user_id, nickname, stat.daily_max_score)
    
    # 重新从Redis获取
    return redis_manager.get_daily_ranking(date, limit)
