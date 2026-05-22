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
        """设置对局状态（Hash 类型）"""
        key = f"match:{match_id}:state"
        # 转换需要序列化的字段
        state_copy = state.copy()
        if "dice_values" in state_copy:
            state_copy["dice_values"] = json.dumps(state_copy["dice_values"])
        if "locked_dice" in state_copy:
            state_copy["locked_dice"] = json.dumps(state_copy["locked_dice"])
        if "selectable_scores" in state_copy:
            state_copy["selectable_scores"] = json.dumps(state_copy["selectable_scores"])
        self.redis.hset(key, mapping=state_copy)

    def get_match_state(self, match_id: str) -> Optional[dict]:
        """获取对局状态（Hash 类型）"""
        key = f"match:{match_id}:state"
        data = self.redis.hgetall(key)
        if not data:
            return None
        
        # 转换类型（Redis已配置decode_responses=True，数据已是字符串）
        result = {}
        for k, v in data.items():
            k_str = k  # 已是字符串，无需decode
            v_str = v  # 已是字符串，无需decode
            
            # 尝试转换为整数
            try:
                result[k_str] = int(v_str)
                continue
            except ValueError:
                pass
            
            # 尝试转换为 JSON
            try:
                result[k_str] = json.loads(v_str)
                continue
            except (json.JSONDecodeError, ValueError):
                pass
            
            # 保持字符串
            result[k_str] = v_str
        
        return result


    def init_player_data(self, match_id: int, user_id: int):
        """初始化玩家数据（使用 Hash 类型）"""
        key = f"match:{match_id}:player:{user_id}"
        # 初始化字段
        self.redis.hset(key, mapping={
            "dice_values": json.dumps([]),
            "locked_dice": json.dumps([]),
            "used_scores": json.dumps([]),
            "total_score": 0
        })
    
    def get_player_data(self, match_id: int, user_id: int) -> Optional[dict]:
        """获取玩家所有数据"""
        key = f"match:{match_id}:player:{user_id}"
        data = self.redis.hgetall(key)
        if not data:
            return None
        
        # 转换类型（Redis已配置decode_responses=True，数据已是字符串）
        return {
            "dice_values": json.loads(data.get("dice_values", "[]")),
            "locked_dice": json.loads(data.get("locked_dice", "[]")),
            "used_scores": json.loads(data.get("used_scores", "[]")),
            "total_score": int(data.get("total_score", "0"))
        }
    
    def update_player_dice(self, match_id: int, user_id: int, dice_values: List[int], locked_dice: List[bool]):
        """更新玩家骰子数据"""
        key = f"match:{match_id}:player:{user_id}"
        self.redis.hset(key, mapping={
            "dice_values": json.dumps(dice_values),
            "locked_dice": json.dumps(locked_dice)
        })
    
    def add_player_score(self, match_id: int, user_id: int, score_type: str, score: int):
        """添加玩家得分，更新已用计分项和总分"""
        key = f"match:{match_id}:player:{user_id}"
        
        # 获取当前数据
        data = self.get_player_data(match_id, user_id)
        if not data:
            return
        
        # 更新已用计分项列表
        used_scores = data["used_scores"]
        if score_type not in used_scores:
            used_scores.append(score_type)
        
        # 更新总分
        total_score = data["total_score"] + score
        
        # 保存到 Redis
        self.redis.hset(key, mapping={
            "used_scores": json.dumps(used_scores),
            "total_score": total_score
        })

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
