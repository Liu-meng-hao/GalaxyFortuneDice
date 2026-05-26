from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from websocket.manager import manager
from sqlalchemy.orm import Session
from config.db_config import get_db
from utils.security import get_current_user_websocket

router = APIRouter()


@router.websocket("/ws/match/{match_id}/{user_id}")
async def match_websocket(
    websocket: WebSocket,
    match_id: int,
    user_id: int,
    token: str,
    db: Session = Depends(get_db)
):
    # =========================
    # WebSocket 鉴权
    # =========================
    user = await get_current_user_websocket(websocket, token, db)
    if user is None:
        return
    
    # 验证 token 中的用户 ID 是否与路径中的 user_id 匹配
    if user.id != user_id:
        await websocket.close(code=1008)
        return

    print(f"用户 {user_id} 尝试连接对局 {match_id}")

    # =========================
    # 建立 websocket连接
    # =========================

    await manager.connect(
        user_id,
        websocket
    )

    # =========================
    # 加入对局频道
    # =========================

    manager.join_channel(
        f"match:{match_id}",
        user_id
    )

    print(f"用户 {user_id} 成功进入对局 {match_id}")

    try:

        while True:

            # 接收客户端消息
            data = await websocket.receive_json()

            message_type = data.get("type")

            # =========================
            # 心跳检测
            # =========================

            if message_type == "ping":

                await manager.send_to_user(
                    user_id,
                    {
                        "type": "pong"
                    }
                )

            # =========================
            # 客户端主动同步动作
            # =========================

            elif message_type == "player_action":

                await manager.broadcast(
                    f"match:{match_id}",
                    {
                        "type": "player_action",
                        "data": data.get("data")
                    },
                    exclude_user_id=user_id
                )

    except WebSocketDisconnect:

        print(f"用户 {user_id} 离开对局 {match_id}")

        # =========================
        # 离开频道
        # =========================
        manager.leave_channel(
            f"match:{match_id}",
            user_id
        )

        # =========================
        # websocket断开
        # =========================
        manager.disconnect(user_id)

        # =========================
        # 广播掉线
        # =========================
        await manager.broadcast(
            f"match:{match_id}",
            {
                "type": "player_disconnect",
                "data": {
                    "user_id": user_id
                }
            }
        )
