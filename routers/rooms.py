from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from config.db_config import get_db, get_redis
from models.user import User
from utils.security import get_current_user
from schemas.room import RoomCreate, RoomJoin, RoomLeave, RoomResponse, PlayerReady
from schemas.user import UserResponse
from crud.room import create_room, get_room_by_id, get_all_rooms, update_room_status
from crud.user import get_user_by_id
from crud.redis_manager import RedisManager
from websocket.manager import manager
from utils.response import success

router = APIRouter(prefix="/api/room", tags=["房间"])

# 创建房间接口
@router.post("/create", response_model=RoomResponse)
async def create_rooms(room_data: RoomCreate, db: Session = Depends(get_db), redis = Depends(get_redis), current_user: User = Depends(get_current_user)):
    room = create_room(db, room_data.game_mode, room_data.max_players, room_data.user_id)
    redis_manager = RedisManager(redis)

    user = get_user_by_id(db, room_data.user_id)
    if user:
        # 创建者的玩家数据
        player_data = {
            "user_id": user.id,
            "nickname": user.nickname,
            "avatar": user.avatar,
            "team_id": 1,
            "seat_no": 1,
            "ready_status": True,
            "is_online": True
        }
        redis_manager.set_room_players(room.room_id, [player_data])
    players = redis_manager.get_room_players(room.room_id)
    return success(RoomResponse(
        room_id=room.room_id,
        game_mode=room.game_mode,
        current_players=len(players),
        max_players=room.max_players,
        creator_id=room.creator_id,
        room_status=room.room_status,
        players=players
    ), msg="创建房间成功")

# 加入房间接口
@router.post("/join")
async def join_room(room_data: RoomJoin, db: Session = Depends(get_db), redis = Depends(get_redis), current_user: User = Depends(get_current_user)):
    room = get_room_by_id(db, room_data.room_id)
    if not room:
        raise HTTPException(status_code=404, detail="房间不存在")
    if room.room_status == 2:
        raise HTTPException(status_code=400, detail="房间已开始游戏")
    if room.room_status == 4:
        raise HTTPException(status_code=400, detail="房间已解散")
    redis_manager = RedisManager(redis)
    players = redis_manager.get_room_players(room_data.room_id)
    
    if len(players) >= room.max_players:
        raise HTTPException(status_code=400, detail="房间已满")
    

    user = get_user_by_id(db, room_data.user_id)

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    player_data = {
        "user_id": user.id,
        "nickname": user.nickname,
        "avatar": user.avatar,
        "exp": user.exp,
        "team_id": 2 if len(players) >= 2 and room.game_mode == 4 else 1,
        "seat_no": len(players) + 1,
        "ready_status": False,
        "is_online": True
    }
    players.append(player_data)
    redis_manager.set_room_players(room_data.room_id, players)
       
    # 广播玩家进入房间
    await manager.broadcast(
        f"room:{room_data.room_id}",
        {
            "type": "player_join",
            "data": player_data
        }
        
    )    
    return success(RoomResponse(
        room_id=room.room_id,
        game_mode=room.game_mode,
        current_players=len(players),
        max_players=room.max_players,
        creator_id=room.creator_id,
        room_status=room.room_status,
        players=players
    ), msg="加入房间成功")

# 离开房间接口
@router.post("/leave")
async def leave_room(room_data: RoomLeave, db: Session = Depends(get_db), redis = Depends(get_redis), current_user: User = Depends(get_current_user)):
    redis_manager = RedisManager(redis)
    # 房主离开房间
    room = get_room_by_id(db,room_data.room_id)
    if not room:
        raise HTTPException(status_code=404, detail="房间不存在")
    if room.creator_id == room_data.user_id:
        # 解散房间
        redis_manager.delete_room_players(room_data.room_id)
        update_room_status(db, room_data.room_id, 4)
        # 广播房间解散
        await manager.broadcast(
            f"room:{room_data.room_id}", 
            {
                "type": "room_disissolve",
                "data": {
                    "room_id": room_data.room_id
                }
            }
        )

    players = redis_manager.get_room_players(room_data.room_id)
    players = [p for p in players if p["user_id"] != room_data.user_id]
    redis_manager.set_room_players(room_data.room_id, players)
    
    # 广播玩家离开房间
    await manager.broadcast(
        f"room:{room_data.room_id}",
        {
            "type": "player_leave",
            "data": {
                "user_id": room_data.user_id
            }
        }
    )
    return success(msg="已离开房间")

# 获取房间列表接口（暂不使用）
@router.get("/list")
async def list_rooms(db: Session = Depends(get_db), redis = Depends(get_redis), current_user: User = Depends(get_current_user)):
    rooms = get_all_rooms(db)
    redis_manager = RedisManager(redis)
    room_responses = []
    for room in rooms:
        players = redis_manager.get_room_players(room.room_id)
        player_responses = []
        for p in players:
            user = get_user_by_id(db, p["user_id"])
            if user:
                player_responses.append(UserResponse.model_validate(user))
        room_responses.append(RoomResponse(
            room_id=room.room_id,
            game_mode=room.game_mode,
            current_players=len(players),
            max_players=room.max_players,
            creator_id=room.creator_id,
            room_status=room.room_status,
            players=player_responses
        ))
    return success(room_responses, msg="获取房间列表成功")
    
# 玩家状态更新接口
@router.post("/player/ready")
async def player_ready(ready_data: PlayerReady, db: Session = Depends(get_db), redis = Depends(get_redis), current_user: User = Depends(get_current_user)):
    redis_manager = RedisManager(redis)
    
    # 获取房间玩家列表
    players = redis_manager.get_room_players(ready_data.room_id)
    
    # 修改用户的 ready_status
    for player in players:
        if player["user_id"] == ready_data.user_id:
            player["ready_status"] = ready_data.ready_status
            break
    
    # 保存回 Redis
    redis_manager.set_room_players(ready_data.room_id, players)
    
    # 获取房间信息，判断调用者是否是房主
    room = get_room_by_id(db, ready_data.room_id)
    if not room:
        raise HTTPException(status_code=404, detail="房间不存在")
    
    # 广播玩家状态更新
    await manager.broadcast(
        f"room:{ready_data.room_id}", 
        {
            "type": "player_ready",
            "data": {
                "user_id": ready_data.user_id,
                "ready_status": ready_data.ready_status
            }
        },
        room.creator_id
    )


    # 仅当房主调用此接口时，判断房间内所有用户的 ready_status 是否都为 True
    if room.creator_id == ready_data.user_id:
        all_ready = all(player.get("ready_status", False) for player in players)
        if all_ready and len(players) >= room.max_players:
            # 所有玩家都准备就绪，开始游戏
            update_room_status(db, ready_data.room_id, 2)
            # 广播游戏开始
            await manager.broadcast(
                f"room:{ready_data.room_id}", 
                {
                    "type": "game_start",
                    "data": {
                        "room_id": ready_data.room_id
                    }
                }
            )
            return success({"is_all_ready": True}, msg="游戏开始")
        return success({"is_all_ready": False}, msg="等待其他玩家准备")
    
    return success(msg="状态已更新")
