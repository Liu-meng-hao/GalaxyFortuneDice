from fastapi import FastAPI
from config.db_config import engine, Base
from models.user import User
from models.room import Room
from models.match import Match, GameRecord
from routers import users, rooms, matches, ranking

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Galaxy Fortune Dice API", description="银河幸运骰子游戏后端接口")

app.include_router(users.router)
app.include_router(rooms.router)
app.include_router(matches.router)
app.include_router(ranking.router)

@app.get("/")
async def root():
    return {"message": "欢迎使用银河幸运骰子API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
