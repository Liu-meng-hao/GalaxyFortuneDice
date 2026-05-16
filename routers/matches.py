from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import random
from config.db_config import get_db, get_redis
from schemas.users import (
    MatchStart, MatchState, RollDice, RollDiceResponse,
    SelectScore, SelectScoreResponse, UserResponse, GameRecordResponse
)
from crud.users import (
    create_match, get_match_by_id, create_game_record,
    get_game_records_by_match, get_user_by_id, RedisManager, update_user_total_score
)

router = APIRouter(prefix="/api/match", tags=["对局"])

SCORE_TYPES = ["ones", "twos", "threes", "fours", "fives", "sixes",
               "three_of_a_kind", "four_of_a_kind", "full_house",
               "small_straight", "large_straight", "yahtzee", "chance"]

@router.post("/start", response_model=MatchState)
async def start_match(match_data: MatchStart, db: Session = Depends(get_db), redis = Depends(get_redis)):
    match = create_match(db, match_data.room_id)
    redis_manager = RedisManager(redis)
    
    room_players = redis_manager.get_room_players(match_data.room_id)
    if room_players:
        first_player_id = room_players[0]["id"]
    else:
        first_player_id = 0
    
    match_state = {
        "match_id": match.match_id,
        "current_round": 1,
        "current_turn_user_id": first_player_id,
        "phase": "rolling",
        "status": "ongoing"
    }
    redis_manager.set_match_state(match.match_id, match_state)
    
    for player in room_players:
        redis_manager.set_player_scores(match.match_id, player["id"], {})
    
    user = get_user_by_id(db, first_player_id)
    user_response = UserResponse.model_validate(user) if user else None
    
    return MatchState(
        match_id=match.match_id,
        current_round=1,
        current_turn_user=user_response,
        phase="rolling",
        selectable_scores=SCORE_TYPES
    )

@router.get("/state", response_model=MatchState)
async def get_match_state(match_id: str, db: Session = Depends(get_db), redis = Depends(get_redis)):
    redis_manager = RedisManager(redis)
    state = redis_manager.get_match_state(match_id)
    if not state:
        raise HTTPException(status_code=404, detail="对局不存在")
    
    user = get_user_by_id(db, state["current_turn_user_id"])
    user_response = UserResponse.model_validate(user) if user else None
    
    return MatchState(
        match_id=state["match_id"],
        current_round=state["current_round"],
        current_turn_user=user_response,
        phase=state["phase"],
        selectable_scores=SCORE_TYPES
    )

@router.post("/roll_dice", response_model=RollDiceResponse)
async def roll_dice(roll_data: RollDice, db: Session = Depends(get_db), redis = Depends(get_redis)):
    redis_manager = RedisManager(redis)
    state = redis_manager.get_match_state(roll_data.match_id)
    if not state:
        raise HTTPException(status_code=404, detail="对局不存在")
    
    dice_state = redis_manager.get_dice_state(roll_data.match_id)
    if not dice_state:
        dice_values = [random.randint(1, 6) for _ in range(5)]
        remain_throws = 2
    else:
        dice_values = dice_state["dice_values"].copy()
        remain_throws = dice_state["remain_throws"]
        
        if remain_throws <= 0:
            raise HTTPException(status_code=400, detail="投掷次数已用完")
        
        if roll_data.lock_mask:
            for i in range(5):
                if not roll_data.lock_mask[i]:
                    dice_values[i] = random.randint(1, 6)
        else:
            dice_values = [random.randint(1, 6) for _ in range(5)]
        
        remain_throws -= 1
    
    redis_manager.set_dice_state(roll_data.match_id, dice_values, remain_throws)
    
    if remain_throws == 0:
        state["phase"] = "scoring"
        redis_manager.set_match_state(roll_data.match_id, state)
    
    return RollDiceResponse(dice_values=dice_values, remain_throw_count=remain_throws)

@router.post("/select_score", response_model=SelectScoreResponse)
async def select_score(score_data: SelectScore, db: Session = Depends(get_db), redis = Depends(get_redis)):
    redis_manager = RedisManager(redis)
    state = redis_manager.get_match_state(score_data.match_id)
    if not state:
        raise HTTPException(status_code=404, detail="对局不存在")
    
    dice_state = redis_manager.get_dice_state(score_data.match_id)
    if not dice_state:
        raise HTTPException(status_code=400, detail="请先投掷骰子")
    
    dice_values = dice_state["dice_values"]
    round_score = calculate_score(dice_values, score_data.score_type)
    
    player_scores = redis_manager.get_player_scores(score_data.match_id, score_data.user_id) or {}
    player_scores[score_data.score_type] = round_score
    total_score = sum(player_scores.values())
    redis_manager.set_player_scores(score_data.match_id, score_data.user_id, player_scores)
    
    create_game_record(
        db,
        score_data.match_id,
        score_data.user_id,
        state["current_round"],
        score_data.score_type,
        round_score,
        total_score
    )
    
    update_user_total_score(db, score_data.user_id, round_score)
    
    redis_manager.update_total_ranking(score_data.user_id, "", total_score)
    
    room_players = redis_manager.get_room_players(state["room_id"])
    current_index = next((i for i, p in enumerate(room_players) if p["id"] == score_data.user_id), 0)
    next_index = (current_index + 1) % len(room_players) if room_players else 0
    
    if next_index == 0:
        state["current_round"] += 1
        if state["current_round"] > 13:
            state["status"] = "finished"
    
    state["current_turn_user_id"] = room_players[next_index]["id"] if room_players else 0
    state["phase"] = "rolling"
    redis_manager.set_match_state(score_data.match_id, state)
    
    redis_manager.set_dice_state(score_data.match_id, [], 3)
    
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
        if any(c >= 3 for c in counts):
            return sum(dice)
        return 0
    elif score_type == "four_of_a_kind":
        if any(c >= 4 for c in counts):
            return sum(dice)
        return 0
    elif score_type == "full_house":
        has_three = any(c == 3 for c in counts)
        has_two = any(c == 2 for c in counts)
        if has_three and has_two:
            return 25
        return 0
    elif score_type == "small_straight":
        straights = [{1,2,3,4}, {2,3,4,5}, {3,4,5,6}]
        dice_set = set(dice)
        for s in straights:
            if s.issubset(dice_set):
                return 30
        return 0
    elif score_type == "large_straight":
        if dice_sorted == [1,2,3,4,5] or dice_sorted == [2,3,4,5,6]:
            return 40
        return 0
    elif score_type == "yahtzee":
        if any(c == 5 for c in counts):
            return 50
        return 0
    elif score_type == "chance":
        return sum(dice)
    else:
        return 0
