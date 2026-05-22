from collections import defaultdict
from fastapi import WebSocket


class ConnectionManager:

    def __init__(self):

        # 所有 websocket 连接
        # {
        #     user_id: websocket
        # }
        self.connections = {}

        # 频道系统
        # {
        #     "room:1001": {1,2,3},
        #     "game:9001": {1,2,3},
        #     "team:1": {1,2},
        #     "global": {1,2,3,4}
        # }
        self.channels = defaultdict(set)

    # =========================
    # websocket 连接
    # =========================

    async def connect(
        self,
        user_id: int,
        websocket: WebSocket
    ):
        """
        用户建立 websocket 连接
        """

        await websocket.accept()

        self.connections[user_id] = websocket

        print(f"用户 {user_id} websocket连接成功")

    # =========================
    # websocket 断开
    # =========================

    def disconnect(self, user_id: int):
        """
        用户 websocket 断开
        """

        # 删除 websocket连接
        self.connections.pop(user_id, None)

        # 从所有频道中移除
        for channel in list(self.channels.keys()):

            self.channels[channel].discard(user_id)

            # 空频道删除
            if not self.channels[channel]:
                del self.channels[channel]

        print(f"用户 {user_id} websocket断开")

    # =========================
    # 加入频道
    # =========================

    def join_channel(
        self,
        channel: str,
        user_id: int
    ):
        """
        用户加入频道
        """

        self.channels[channel].add(user_id)

        print(f"用户 {user_id} 加入频道 {channel}")

    # =========================
    # 离开频道
    # =========================

    def leave_channel(
        self,
        channel: str,
        user_id: int
    ):
        """
        用户离开频道
        """

        if channel not in self.channels:
            return

        self.channels[channel].discard(user_id)

        # 空频道删除
        if not self.channels[channel]:
            del self.channels[channel]

        print(f"用户 {user_id} 离开频道 {channel}")

    # =========================
    # 频道广播
    # =========================

    async def broadcast(
        self,
        channel: str,
        message: dict,
        exclude_user_id: int = None
    ):
        """
        频道广播
        """

        if channel not in self.channels:
            return

        disconnected_users = []

        for user_id in self.channels[channel]:

            # 排除自己
            if exclude_user_id == user_id:
                continue

            websocket = self.connections.get(user_id)

            if not websocket:
                continue

            try:

                await websocket.send_json(message)

            except Exception as e:

                print(f"广播失败 user_id={user_id}, error={e}")

                disconnected_users.append(user_id)

        # 清理断开的用户
        for user_id in disconnected_users:
            self.disconnect(user_id)

    # =========================
    # 单用户发送
    # =========================

    async def send_to_user(
        self,
        user_id: int,
        message: dict
    ):
        """
        单播消息
        """

        websocket = self.connections.get(user_id)

        if not websocket:
            return

        try:

            await websocket.send_json(message)

        except Exception as e:

            print(f"发送失败 user_id={user_id}, error={e}")

            self.disconnect(user_id)

    # =========================
    # 获取频道人数
    # =========================

    def get_channel_users(self, channel: str):

        return list(self.channels.get(channel, set()))

    # =========================
    # 判断用户是否在线
    # =========================

    def is_online(self, user_id: int):

        return user_id in self.connections


# 全局 websocket管理器
manager = ConnectionManager()