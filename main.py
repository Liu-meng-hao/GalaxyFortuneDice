from fastapi import FastAPI
from config.db_config import engine, Base
from models.user import User
from models.room import Room
from models.match import Match, MatchScoreSheet, GameRecord
from models.stats import UserHistoryStats, UserDailyStats
from routers import users, rooms, matches, ranking
from websocket.room_ws import router as ws_room_router
from websocket.match_ws import router as ws_match_router
from fastapi.middleware.cors import CORSMiddleware



Base.metadata.create_all(bind=engine)

app = FastAPI(title="Galaxy Fortune Dice API", description="银河幸运骰子游戏后端接口")

app.include_router(users.router)
app.include_router(rooms.router)
app.include_router(matches.router)
app.include_router(ranking.router)
app.include_router(ws_room_router)
app.include_router(ws_match_router)

ALLOW_ORIGINS = [
    "http://localhost:3000",   # React/Vue3默认端口
    "http://localhost:5173",   # Vite默认端口
    "http://localhost:8080",   # Vue CLI旧版端口
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8080",
    "http://127.0.0.1:8000",
]
# 配置CORS跨域规则
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS,
    allow_credentials=True,  # 允许携带Cookie/Token
    allow_methods=["*"],  # 允许所有请求方法 GET/POST/PUT/DELETE
    allow_headers=["*"],  # 允许所有请求头
)

@app.get("/")
async def root():
    return {"message": "欢迎使用银河幸运骰子API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
