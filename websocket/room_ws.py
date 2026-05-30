from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from websocket.manager import manager
from sqlalchemy.orm import Session
from config.db_config import get_db, get_redis
from utils.security import get_current_user_websocket
from crud.redis_manager import RedisManager
from models.user import User

router = APIRouter()


@router.websocket("/ws/room/{room_id}")
async def room_websocket(
    websocket: WebSocket,
    room_id: int,
    token: str,
    db: Session = Depends(get_db),
    redis = Depends(get_redis)
):
    # =========================
    # WebSocket 鉴权
    # =========================
    user = await get_current_user_websocket(websocket, token, db)
    if user is None:
        return

    user_id = user.id

    print(f"用户 {user_id} 尝试连接房间 {room_id}")

    # =========================
    # 建立 websocket连接
    # =========================

    await manager.connect(
        user_id,
        websocket
    )

    # =========================
    # 加入房间频道
    # =========================

    manager.join_channel(
        f"room:{room_id}",
        user_id
    )

    # =========================
    # 同步房间状态，防止漏掉连接前的广播
    # =========================

    redis_manager = RedisManager(redis)
    players = redis_manager.get_room_players(room_id)
    await manager.send_to_user(user_id, {
        "type": "room_sync",
        "data": {
            "room_id": room_id,
            "players": players
        }
    })

    print(f"用户 {user_id} websocket连接成功，已同步房间状态")

    try:

        while True:

            # 保持 websocket连接
            await websocket.receive_text()

    except WebSocketDisconnect:

        print(f"用户 {user_id} websocket断开")

        # =========================
        # 离开房间频道
        # =========================

        manager.leave_channel(
            f"room:{room_id}",
            user_id
        )

        # =========================
        # websocket断开
        # =========================

        manager.disconnect(user_id)

        # =========================
        # 广播掉线事件
        # =========================

        await manager.broadcast(
            f"room:{room_id}",
            {
                "type": "player_disconnect",
                "data": {
                    "user_id": user_id
                }
            }
        )
