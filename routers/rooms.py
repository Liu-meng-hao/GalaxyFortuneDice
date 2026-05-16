from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from config.db_config import get_db, get_redis
from schemas.room import RoomCreate, RoomJoin, RoomLeave, RoomResponse, PlayerReady, RoomIdResponse, PlayersReadyResponse
from schemas.user import UserResponse, MessageResponse
from crud.room import create_room, get_room_by_id, get_all_rooms
from crud.user import get_user_by_id
from crud.redis_manager import RedisManager

router = APIRouter(prefix="/api/room", tags=["房间"])

@router.post("/create", response_model=RoomIdResponse)
async def create_room_endpoint(room_data: RoomCreate, db: Session = Depends(get_db), redis = Depends(get_redis)):
    room = create_room(db, room_data.game_mode, room_data.max_players, room_data.user_id)
    redis_manager = RedisManager(redis)
    user = get_user_by_id(db, room_data.user_id)
    if user:
        player_data = {
            "id": user.id,
            "nickname": user.nickname,
            "avatar": user.avatar
        }
        redis_manager.set_room_players(room.room_id, [player_data])
    return {"room_id": room.room_id}

@router.post("/join", response_model=RoomResponse)
async def join_room(room_data: RoomJoin, db: Session = Depends(get_db), redis = Depends(get_redis)):
    room = get_room_by_id(db, room_data.room_id)
    if not room:
        raise HTTPException(status_code=404, detail="房间不存在")
    if room.status != "waiting":
        raise HTTPException(status_code=400, detail="房间已开始游戏")
    
    redis_manager = RedisManager(redis)
    players = redis_manager.get_room_players(room_data.room_id)
    
    if len(players) >= room.max_players:
        raise HTTPException(status_code=400, detail="房间已满")
    
    if any(p["id"] == room_data.user_id for p in players):
        raise HTTPException(status_code=400, detail="已在房间中")
    
    user = get_user_by_id(db, room_data.user_id)
    if user:
        player_data = {
            "id": user.id,
            "nickname": user.nickname,
            "avatar": user.avatar
        }
        players.append(player_data)
        redis_manager.set_room_players(room_data.room_id, players)
    
    player_responses = [UserResponse(**p, is_guest=False, total_score=0, created_at="2024-01-01T00:00:00") for p in players]
    return RoomResponse(
        room_id=room.room_id,
        game_mode=room.game_mode,
        max_players=room.max_players,
        owner_id=room.owner_id,
        status=room.status,
        players=player_responses
    )

@router.post("/leave", response_model=MessageResponse)
async def leave_room(room_data: RoomLeave, db: Session = Depends(get_db), redis = Depends(get_redis)):
    redis_manager = RedisManager(redis)
    players = redis_manager.get_room_players(room_data.room_id)
    players = [p for p in players if p["id"] != room_data.user_id]
    redis_manager.set_room_players(room_data.room_id, players)
    return {"message": "已离开房间"}

@router.get("/list", response_model=List[RoomResponse])
async def list_rooms(db: Session = Depends(get_db), redis = Depends(get_redis)):
    rooms = get_all_rooms(db)
    redis_manager = RedisManager(redis)
    room_responses = []
    for room in rooms:
        players = redis_manager.get_room_players(room.room_id)
        player_responses = []
        for p in players:
            user = get_user_by_id(db, p["id"])
            if user:
                player_responses.append(UserResponse.model_validate(user))
        room_responses.append(RoomResponse(
            room_id=room.room_id,
            game_mode=room.game_mode,
            max_players=room.max_players,
            owner_id=room.owner_id,
            status=room.status,
            players=player_responses
        ))
    return room_responses

@router.post("/player/ready", response_model=MessageResponse)
async def player_ready(ready_data: PlayerReady, db: Session = Depends(get_db), redis = Depends(get_redis)):
    redis_manager = RedisManager(redis)
    redis_manager.set_player_ready(ready_data.room_id, ready_data.user_id, ready_data.ready_status)
    return {"message": "状态已更新"}

@router.get("/player/info", response_model=PlayersReadyResponse)
async def get_players_info(room_id: str, redis = Depends(get_redis)):
    redis_manager = RedisManager(redis)
    players_ready = redis_manager.get_players_ready(room_id)
    return {"players_ready": players_ready}
