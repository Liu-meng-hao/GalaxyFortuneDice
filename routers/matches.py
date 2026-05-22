from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import random
from datetime import datetime
from config.db_config import get_db, get_redis
from schemas.match import (
    MatchStart, MatchState, MatchStartResponse, MatchUserInfo,
    RollDice, RollDiceResponse, SelectScore, SelectScoreResponse, GameRecordResponse
)
from schemas.user import UserResponse
from crud.match import create_match, create_game_record, get_game_records_by_match, create_match_score_sheet, update_match
from crud.user import get_user_by_id, update_user_total_score, update_user_history_stats, update_user_daily_stats
from crud.redis_manager import RedisManager

router = APIRouter(prefix="/api/match", tags=["对局"])

# 计分项类型列表
SCORE_TYPES = [
    "ones", "twos", "threes", "fours", "fives", "sixes",
    "three_of_a_kind", "four_of_a_kind", "full_house",
    "small_straight", "large_straight", "yahtzee", "chance"
]

@router.post("/start", response_model=MatchStartResponse)
async def start_match(match_data: MatchStart, db: Session = Depends(get_db), redis = Depends(get_redis)):
    match = create_match(db, match_data.room_id)
    redis_manager = RedisManager(redis) 
    room_players = redis_manager.get_room_players(match_data.room_id) # 获取房间中的玩家玩家信息
    
    # 随机选择起始玩家索引
    start_index = random.randint(0, len(room_players)-1) if room_players else 0
    first_player = room_players[start_index] if room_players else None
    first_player_id = first_player["user_id"] if first_player else 0
    first_seat_no = first_player["seat_no"] if first_player else 0
    
    # 初始化对局状态并存储到 Redis（包含骰子字段）
    match_state = {
        "match_id": match.id,
        "room_id": match_data.room_id,
        "current_round": 1,
        "current_turn_user_id": first_player_id,
        "current_seat_no": first_seat_no,
        "phase": "THROWING",
        "remain_throw_count": 3,
        "dice_values": [],
        "locked_dice": [],
        "selectable_scores": []
    }
    redis_manager.set_match_state(match.id, match_state)
    
    # 初始化每个玩家的实时数据
    for player in room_players:
        redis_manager.init_player_data(match.id, player["user_id"])
    
    # 构建玩家信息
    match_info = []
    for player in room_players:
        match_info.append(MatchUserInfo(
            user_id=player.get("user_id", 0),
            nickname=player.get("nickname", ""),
            team_id=player.get("team_id", 0),
            seat_no=player.get("seat_no", 0),
            ready_status=player.get("ready_status", False),
            is_online=player.get("is_online", True)
        ))
    
    return MatchStartResponse(id=match.id, match_info=match_info)

@router.get("/state", response_model=MatchState)
async def get_match_state(match_id: int, db: Session = Depends(get_db), redis = Depends(get_redis)):
    redis_manager = RedisManager(redis)
    state = redis_manager.get_match_state(match_id)
    if not state:
        raise HTTPException(status_code=404, detail="对局不存在")
    
    return MatchState(
        match_id=match_id,
        room_id=state.get("room_id", 0),
        current_round=state.get("current_round", 1),
        current_turn_user_id=state.get("current_turn_user_id", 0),
        current_seat_no=state.get("current_seat_no", 0),
        phase=state.get("phase", "THROWING"),
        remain_throw_count=state.get("remain_throw_count", 3),
        dice_values=state.get("dice_values", []),
        locked_dice=state.get("locked_dice", []),
        selectable_scores=state.get("selectable_scores", [])
    )

@router.post("/roll_dice", response_model=RollDiceResponse)
async def roll_dice(roll_data: RollDice, db: Session = Depends(get_db), redis = Depends(get_redis)):
    redis_manager = RedisManager(redis)
    state = redis_manager.get_match_state(roll_data.match_id)
    if not state:
        raise HTTPException(status_code=404, detail="对局不存在")
    
    # 从对局状态获取骰子信息
    remain_throws = state.get("remain_throw_count", 3)
    current_dice = state.get("dice_values", [])
    
    if remain_throws <= 0:
        raise HTTPException(status_code=400, detail="投掷次数已用完")
    
    # 生成骰子值
    if not current_dice:
        # 第一次投掷
        dice_values = [random.randint(1, 6) for _ in range(5)]
    else:
        # 后续投掷，根据锁定状态更新
        dice_values = current_dice.copy()
        if roll_data.lock_mask:
            for i in range(5):
                if not roll_data.lock_mask[i]:
                    dice_values[i] = random.randint(1, 6)
        else:
            dice_values = [random.randint(1, 6) for _ in range(5)]
    
    # 更新对局状态中的骰子信息
    remain_throws -= 1
    state["remain_throw_count"] = remain_throws
    state["dice_values"] = dice_values
    state["locked_dice"] = roll_data.lock_mask or []
    
    # 获取当前玩家已选择的计分项
    player_data = redis_manager.get_player_data(roll_data.match_id, roll_data.user_id) or {}
    selected_types = set(player_data.get("used_scores", []))
    
    # 计算可选分数，过滤已选的类型
    selectable_scores = []
    for score_type in SCORE_TYPES:
        if score_type not in selected_types:
            score = calculate_score(dice_values, score_type)
            selectable_scores.append({"type": score_type, "score": score})
    
    state["selectable_scores"] = selectable_scores
    state["phase"] = "SELECTING"
    redis_manager.set_match_state(roll_data.match_id, state)
    
    return RollDiceResponse(dice_values=dice_values, remain_throw_count=remain_throws)

@router.post("/select_score", response_model=SelectScoreResponse)
async def select_score(score_data: SelectScore, db: Session = Depends(get_db), redis = Depends(get_redis)):
    redis_manager = RedisManager(redis)
    state = redis_manager.get_match_state(score_data.match_id)
    if not state:
        raise HTTPException(status_code=404, detail="对局不存在")
    
    # 从对局状态获取骰子信息
    dice_values = state.get("dice_values", [])
    if not dice_values:
        raise HTTPException(status_code=400, detail="请先投掷骰子")
    
    round_score = calculate_score(dice_values, score_data.score_type)
    
    # 添加玩家得分（更新已用计分项和总分）
    redis_manager.add_player_score(score_data.match_id, score_data.user_id, score_data.score_type, round_score)
    
    # 获取更新后的玩家数据
    player_data = redis_manager.get_player_data(score_data.match_id, score_data.user_id)
    total_score = player_data["total_score"] if player_data else round_score
    
    # 记录到计分项使用表
    create_match_score_sheet(
        db,
        score_data.match_id,
        score_data.user_id,
        score_data.score_type,
        round_score
    )
    
    update_user_total_score(db, score_data.user_id, round_score)
    
    # 更新排行榜
    redis_manager.update_total_ranking(score_data.user_id, "", total_score)
    
    # 切换到下一个玩家（使用取余循环）
    room_players = redis_manager.get_room_players(state["room_id"])
    player_count = len(room_players)
    
    if player_count == 0:
        raise HTTPException(status_code=400, detail="房间中没有玩家")
    
    # 获取当前玩家的座位号
    current_seat_no = state.get("current_seat_no", 0)
    
    # 找到当前玩家在列表中的索引
    current_index = next((i for i, p in enumerate(room_players) if p["seat_no"] == current_seat_no), 0)
    
    # 使用取余方法计算下一个玩家索引
    next_index = (current_index + 1) % player_count
    
    # 判断是否完成一轮（回到起始玩家）
    if next_index == 0:
        state["current_round"] += 1
        if state["current_round"] > 13:
            state["status"] = "finished"
            
            # 游戏结束，收集所有玩家的最终得分
            player_scores = []
            for player in room_players:
                player_data = redis_manager.get_player_data(score_data.match_id, player["user_id"])
                final_score = player_data["total_score"] if player_data else 0
                player_scores.append({
                    "user_id": player["user_id"],
                    "final_score": final_score
                })
            
            # 按得分降序排序，计算排名
            player_scores.sort(key=lambda x: -x["final_score"])
            for i, ps in enumerate(player_scores):
                rank = i + 1
                is_win = 1 if i == 0 else 0  # 第一名获胜
                
                # 更新游戏战绩表
                create_game_record(
                    db,
                    score_data.match_id,
                    ps["user_id"],
                    ps["final_score"],
                    rank=rank,
                    is_win=is_win
                )
                
                # 更新用户历史统计表
                update_user_history_stats(db, ps["user_id"], ps["final_score"], is_win)
                
                # 更新用户每日统计表
                update_user_daily_stats(db, ps["user_id"], ps["final_score"], is_win)
            
            # 获取获胜者
            winner_user_id = player_scores[0]["user_id"] if player_scores else None
            
            # 更新对局表信息
            update_match(
                db,
                score_data.match_id,
                match_status=2,           # 1=进行中, 2=已结束
                winner_user_id=winner_user_id,
                end_time=datetime.now()
            )
    
    next_player = room_players[next_index]
    
    # 更新对局状态
    state["current_turn_user_id"] = next_player["user_id"]
    state["current_seat_no"] = next_player["seat_no"]
    state["phase"] = "THROWING"
    state["selectable_scores"] = []
    state["remain_throw_count"] = 3
    state["dice_values"] = []
    state["locked_dice"] = []
    redis_manager.set_match_state(score_data.match_id, state)
    
    return SelectScoreResponse(round_score=round_score, total_score=total_score)

@router.get("/final_score", response_model=List[GameRecordResponse])
async def get_final_score(match_id: str, db: Session = Depends(get_db)):
    records = get_game_records_by_match(db, match_id)
    return [GameRecordResponse.model_validate(r) for r in records]

def calculate_score(dice: List[int], score_type: str) -> int:
    dice_sorted = sorted(dice)
    counts = [0] * 7
    for d in dice:
        counts[d] += 1
    
    if score_type == "ones":
        return counts[1] * 1
    elif score_type == "twos":
        return counts[2] * 2
    elif score_type == "threes":
        return counts[3] * 3
    elif score_type == "fours":
        return counts[4] * 4
    elif score_type == "fives":
        return counts[5] * 5
    elif score_type == "sixes":
        return counts[6] * 6
    elif score_type == "three_of_a_kind":
        return sum(dice) if max(counts) >= 3 else 0
    elif score_type == "four_of_a_kind":
        return sum(dice) if max(counts) >= 4 else 0
    elif score_type == "full_house":
        return 25 if (3 in counts and 2 in counts) else 0
    elif score_type == "small_straight":
        return 30 if any(all(x in dice for x in seq) for seq in [[1,2,3,4], [2,3,4,5], [3,4,5,6]]) else 0
    elif score_type == "large_straight":
        return 40 if dice_sorted in [[1,2,3,4,5], [2,3,4,5,6]] else 0
    elif score_type == "yahtzee":
        return 50 if max(counts) == 5 else 0
    elif score_type == "chance":
        return sum(dice)
    return 0
