from fastapi import WebSocket
from collections import defaultdict

class ConnectionManager:

    def __init__(self):
        # 房间连接管理
        # {
        #   room_id: {
        #       user_id: websocket
        #   }
        # }
        self.rooms = defaultdict(dict)

    # 用户连接
    async def connect(self, room_id: int, user_id: int, websocket: WebSocket):
        await websocket.accept()
        self.rooms[room_id][user_id] = websocket

    # 用户断开
    def disconnect(self, room_id: int, user_id: int):
        if room_id in self.rooms:
            self.rooms[room_id].pop(user_id, None)

            # 房间没人了
            if not self.rooms[room_id]:
                del self.rooms[room_id]

    # 广播消息
    async def broadcast(self, room_id: int, message: dict):
        if room_id not in self.rooms:
            return

        disconnected_users = []

        for user_id, websocket in self.rooms[room_id].items():
            try:
                await websocket.send_json(message)
            except:
                disconnected_users.append(user_id)

        # 清理断开的连接
        for user_id in disconnected_users:
            self.disconnect(room_id, user_id)

# 全局 websocket 管理器
manager = ConnectionManager()