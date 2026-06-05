from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from config.db_config import get_redis, get_db
from models.user import User
from utils.security import get_current_user
from schemas.ranking import RankingResponse, RankingItem
from crud.redis_manager import RedisManager
from crud.user import get_user_by_id
from models.stats import UserHistoryStats, UserDailyStats

router = APIRouter(prefix="/api/ranking", tags=["排行榜"])

SORT_TYPES = ["total_games", "wins", "max_score"]


@router.get("/total")
async def get_total_ranking(
    sort_by: str = "max_score",
    page: int = 1,
    page_size: int = 10,
    redis=Depends(get_redis),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if sort_by not in SORT_TYPES:
        raise HTTPException(status_code=400, detail=f"无效的排序类型: {sort_by}，可选值: {SORT_TYPES}")

    offset = (page - 1) * page_size

    if sort_by == "max_score":
        rankings_data = await _get_total_ranking_by_max_score(db, redis, offset, page_size)
    elif sort_by == "wins":
        rankings_data = await _get_total_ranking_by_wins(db, offset, page_size)
    elif sort_by == "total_games":
        rankings_data = await _get_total_ranking_by_total_games(db, offset, page_size)

    rankings = await _build_ranking_items(rankings_data, db, offset)

    return RankingResponse(
        rankings=rankings,
        page=page,
        page_size=page_size,
        sort_by=sort_by
    )


@router.get("/daily")
async def get_daily_ranking(
    date: Optional[str] = None,
    sort_by: str = "max_score",
    page: int = 1,
    page_size: int = 10,
    redis=Depends(get_redis),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if sort_by not in SORT_TYPES:
        raise HTTPException(status_code=400, detail=f"无效的排序类型: {sort_by}，可选值: {SORT_TYPES}")

    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    offset = (page - 1) * page_size

    if sort_by == "max_score":
        rankings_data = await _get_daily_ranking_by_max_score(db, redis, date, offset, page_size)
    elif sort_by == "wins":
        rankings_data = await _get_daily_ranking_by_wins(db, date, offset, page_size)
    elif sort_by == "total_games":
        rankings_data = await _get_daily_ranking_by_total_games(db, date, offset, page_size)

    rankings = await _build_ranking_items(rankings_data, db, offset)

    return RankingResponse(
        rankings=rankings,
        page=page,
        page_size=page_size,
        date=date,
        sort_by=sort_by
    )


async def _get_total_ranking_by_max_score(db: Session, redis, offset: int, limit: int):
    redis_manager = RedisManager(redis)
    rankings_data = redis_manager.get_total_ranking(limit=limit, offset=offset)

    if not rankings_data:
        stats = (
            db.query(UserHistoryStats, User)
            .join(User, UserHistoryStats.user_id == User.id)
            .order_by(UserHistoryStats.max_score.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
        for stat, user in stats:
            redis_manager.update_total_ranking(stat.user_id, user.nickname, stat.max_score)
        rankings_data = redis_manager.get_total_ranking(limit=limit, offset=offset)

    return rankings_data


async def _get_total_ranking_by_wins(db: Session, offset: int, limit: int):
    """按胜场数排序 - 使用正确的字段名 total_wins"""
    stats_with_users = (
        db.query(UserHistoryStats, User)
        .join(User, UserHistoryStats.user_id == User.id)
        .order_by(UserHistoryStats.total_wins.desc())  # 修复：使用 total_wins
        .limit(limit)
        .offset(offset)
        .all()
    )
    return [(f"{stat.user_id}:{user.nickname}:{stat.total_wins}:{stat.total_games}:{stat.max_score}", stat.total_wins) 
            for stat, user in stats_with_users]


async def _get_total_ranking_by_total_games(db: Session, offset: int, limit: int):
    """按总场数排序"""
    stats_with_users = (
        db.query(UserHistoryStats, User)
        .join(User, UserHistoryStats.user_id == User.id)
        .order_by(UserHistoryStats.total_games.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    return [(f"{stat.user_id}:{user.nickname}:{stat.total_wins}:{stat.total_games}:{stat.max_score}", stat.total_games) 
            for stat, user in stats_with_users]


async def _get_daily_ranking_by_max_score(db: Session, redis, date: str, offset: int, limit: int):
    from datetime import datetime as dt
    stat_date = dt.strptime(date, "%Y-%m-%d").date()

    redis_manager = RedisManager(redis)
    rankings_data = redis_manager.get_daily_ranking(date, limit=limit, offset=offset)

    if not rankings_data:
        stats = (
            db.query(UserDailyStats, User)
            .join(User, UserDailyStats.user_id == User.id)
            .filter(UserDailyStats.stat_date == stat_date)
            .order_by(UserDailyStats.daily_max_score.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
        for stat, user in stats:
            redis_manager.update_daily_ranking(date, stat.user_id, user.nickname, stat.daily_max_score)
        rankings_data = redis_manager.get_daily_ranking(date, limit=limit, offset=offset)

    return rankings_data


async def _get_daily_ranking_by_wins(db: Session, date: str, offset: int, limit: int):
    """按当日胜场数排序"""
    from datetime import datetime as dt
    stat_date = dt.strptime(date, "%Y-%m-%d").date()

    stats_with_users = (
        db.query(UserDailyStats, User)
        .join(User, UserDailyStats.user_id == User.id)
        .filter(UserDailyStats.stat_date == stat_date)
        .order_by(UserDailyStats.daily_wins.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    return [(f"{stat.user_id}:{user.nickname}:{stat.daily_wins}:{stat.daily_games}:{stat.daily_max_score}", stat.daily_wins) 
            for stat, user in stats_with_users]


async def _get_daily_ranking_by_total_games(db: Session, date: str, offset: int, limit: int):
    """按当日总场数排序 - 使用正确的字段名 daily_games"""
    from datetime import datetime as dt
    stat_date = dt.strptime(date, "%Y-%m-%d").date()

    stats_with_users = (
        db.query(UserDailyStats, User)
        .join(User, UserDailyStats.user_id == User.id)
        .filter(UserDailyStats.stat_date == stat_date)
        .order_by(UserDailyStats.daily_games.desc())  # 修复：使用 daily_games
        .limit(limit)
        .offset(offset)
        .all()
    )
    return [(f"{stat.user_id}:{user.nickname}:{stat.daily_wins}:{stat.daily_games}:{stat.daily_max_score}", stat.daily_games) 
            for stat, user in stats_with_users]


async def _build_ranking_items(rankings_data, db: Session = None, offset: int = 0):
    """构建排行榜项，包含所有统计数据"""
    rankings = []
    for index, (member, _) in enumerate(rankings_data):
        parts = member.split(":")
        user_id = int(parts[0])
        nickname = parts[1] if len(parts) > 1 else ""
        wins = int(parts[2]) if len(parts) > 2 else 0
        total_games = int(parts[3]) if len(parts) > 3 else 0
        max_score = int(parts[4]) if len(parts) > 4 else 0

        # 如果从Redis获取的数据没有完整字段，尝试从数据库补充
        if len(parts) < 5 and db:
            stat = db.query(UserHistoryStats).filter(UserHistoryStats.user_id == user_id).first()
            if stat:
                wins = stat.total_wins
                total_games = stat.total_games
                max_score = stat.max_score

        # 计算排名 (offset + 索引 + 1)
        rank = offset + index + 1

        rankings.append(RankingItem(
            user_id=user_id,
            nickname=nickname,
            avatar=None,
            rank=rank,
            total_games=total_games,
            wins=wins,
            max_score=max_score
        ))
    return rankings
