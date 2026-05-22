from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from websocket.manager import manager


router = APIRouter()

@router.websocket("/ws/room/{room_id}/{user_id}")
async def room_websocket(
    websocket: WebSocket,
    room_id: int,
    user_id: int
):
    print(f"用户{user_id}尝试连接房间{room_id}")
    # 建立连接
    await manager.connect(room_id, user_id, websocket)
    print(f"用户{user_id}连接成功")
    try:
        while True:
            # 保持连接
            await websocket.receive_text()

    except WebSocketDisconnect:

        # 用户断开
        manager.disconnect(room_id, user_id)

        # 广播离线
        await manager.broadcast(room_id, {
            "type": "player_disconnect",
            "data": {
                "user_id": user_id
            }
        })