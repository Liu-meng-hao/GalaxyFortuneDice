from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from websocket.manager import manager
from models.user import User
from utils.security import get_current_user
from fastapi import Depends

router = APIRouter()


@router.websocket("/ws/match/{match_id}")
async def match_websocket(
    websocket: WebSocket,
    match_id: int,
    current_user: User = Depends(get_current_user)
):
    user_id = current_user.user_id
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