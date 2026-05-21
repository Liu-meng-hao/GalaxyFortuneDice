import json
from typing import List, Optional

class RedisManager:
    def __init__(self, redis_client):
        self.redis = redis_client

    def set_room_players(self, room_id: int, players: List[dict]):
        key = f"room:{room_id}:players"
        self.redis.set(key, json.dumps(players))

    def get_room_players(self, room_id: int) -> List[dict]:
        key = f"room:{room_id}:players"
        data = self.redis.get(key)
        return json.loads(data) if data else []

    def set_match_state(self, match_id: int, state: dict):
        key = f"match:{match_id}:state"
        self.redis.set(key, json.dumps(state))

    def get_match_state(self, match_id: str) -> Optional[dict]:
        key = f"match:{match_id}:state"
        data = self.redis.get(key)
        return json.loads(data) if data else None

    def set_dice_state(self, match_id: str, dice_values: List[int], remain_throws: int):
        key = f"match:{match_id}:dice"
        data = {
            "dice_values": dice_values,
            "remain_throws": remain_throws
        }
        self.redis.set(key, json.dumps(data))

    def get_dice_state(self, match_id: int) -> Optional[dict]:
        key = f"match:{match_id}:dice"
        data = self.redis.get(key)
        return json.loads(data) if data else None

    def set_player_scores(self, match_id: int, user_id: int, scores: dict):
        key = f"match:{match_id}:scores:{user_id}"
        self.redis.set(key, json.dumps(scores))

    def get_player_scores(self, match_id: str, user_id: int) -> Optional[dict]:
        key = f"match:{match_id}:scores:{user_id}"
        data = self.redis.get(key)
        return json.loads(data) if data else None

    def update_total_ranking(self, user_id: int, nickname: str, score: int):
        key = "ranking:total"
        member = f"{user_id}:{nickname}"
        self.redis.zadd(key, {member: score})

    def get_total_ranking(self, limit: int) -> List[tuple]:
        key = "ranking:total"
        return self.redis.zrevrange(key, 0, limit - 1, withscores=True)

    def update_daily_ranking(self, date: str, user_id: int, nickname: str, score: int):
        key = f"ranking:daily:{date}"
        member = f"{user_id}:{nickname}"
        self.redis.zadd(key, {member: score})

    def get_daily_ranking(self, date: str, limit: int) -> List[tuple]:
        key = f"ranking:daily:{date}"
        return self.redis.zrevrange(key, 0, limit - 1, withscores=True)
