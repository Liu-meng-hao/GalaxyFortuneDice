from crud.redis_manager import RedisManager

class RankingCRUD:
    def __init__(self, redis_client):
        self.redis_manager = RedisManager(redis_client)

    def update_total_ranking(self, user_id: int, nickname: str, score: int):
        self.redis_manager.update_total_ranking(user_id, nickname, score)

    def get_total_ranking(self, limit: int):
        return self.redis_manager.get_total_ranking(limit)

    def update_daily_ranking(self, date: str, user_id: int, nickname: str, score: int):
        self.redis_manager.update_daily_ranking(date, user_id, nickname, score)

    def get_daily_ranking(self, date: str, limit: int):
        return self.redis_manager.get_daily_ranking(date, limit)
