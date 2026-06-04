# Galaxy Fortune Dice（银河幸运骰子）

多人在线骰子对战游戏后端，基于 Yahtzee（快艇骰子）规则，支持实时对战、房间管理、排行榜等功能。

## 技术栈

| 组件 | 技术 |
|------|------|
| Web 框架 | FastAPI + Uvicorn |
| 数据库 | MySQL + SQLAlchemy ORM |
| 缓存 | Redis |
| 认证 | JWT (python-jose) + bcrypt |
| 实时通信 | WebSocket |
| 数据校验 | Pydantic v2 |

## 项目结构

```
GalaxyFortuneDice/
├── main.py                  # 应用入口，路由注册、CORS 配置
├── requirements.txt         # Python 依赖
├── config/
│   └── db_config.py         # 数据库/Redis 连接、环境变量配置
├── models/                  # SQLAlchemy ORM 模型
│   ├── user.py              # 用户表
│   ├── room.py              # 房间表
│   ├── match.py             # 对局表、计分表、游戏记录表
│   └── stats.py             # 用户历史统计、每日统计表
├── schemas/                 # Pydantic 请求/响应模型
│   ├── user.py
│   ├── room.py
│   ├── match.py
│   ├── ranking.py
│   └── response.py          # 统一响应格式
├── routers/                 # HTTP API 路由
│   ├── users.py             # 用户注册/登录/信息
│   ├── rooms.py             # 房间创建/加入/离开/准备
│   ├── matches.py           # 对局开始/掷骰/选分/结算
│   └── ranking.py           # 排行榜
├── crud/                    # 数据库操作层
│   ├── user.py
│   ├── room.py
│   ├── match.py
│   ├── ranking.py
│   └── redis_manager.py     # Redis 操作封装
├── utils/                   # 工具函数
│   ├── security.py          # JWT 生成/验证、密码加密
│   ├── response.py          # 统一响应封装
│   └── re.py                # 正则校验
└── websocket/               # WebSocket 实时通信
    ├── manager.py           # 连接管理器（频道系统、广播）
    ├── room_ws.py           # 房间 WebSocket
    └── match_ws.py          # 对局 WebSocket
```

## 环境准备

### 依赖安装

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate    # Linux/Mac
pip install -r requirements.txt
```

### 环境变量配置

在项目根目录创建 `.env` 文件：

```env
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DB=galaxy_dice

REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_DB=0

SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_DAYS=1
```

### 启动服务

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

启动后访问 `http://localhost:8001/docs` 查看 Swagger API 文档。

## 数据库表结构

| 表名 | 说明 |
|------|------|
| `t_users` | 用户信息（手机号、昵称、头像、经验值） |
| `t_room` | 房间信息（房间号、游戏模式、状态） |
| `t_match` | 对局记录（关联房间、游戏模式、胜负） |
| `t_match_score_sheet` | 对局计分明细（每轮每个玩家的得分类型和分数） |
| `t_game_record` | 游戏战绩（最终得分、排名、是否获胜） |
| `user_history_stats` | 用户历史统计（总场次、总胜场、最高分） |
| `user_daily_stats` | 用户每日统计（当日场次、胜场、最高分） |

## API 接口

### 用户 `/api/user`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/register` | 用户注册 |
| POST | `/login` | 用户登录，返回 JWT Token |
| POST | `/guest` | 游客登录，返回 JWT Token（无注册） |

### 房间 `/api/room`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/create` | 创建房间 |
| POST | `/join` | 加入房间 |
| POST | `/leave` | 离开/解散房间 |
| GET | `/list` | 获取房间列表 |
| POST | `/player/ready` | 更新准备状态；房主触发开始时自动创建对局并广播 `match_id` |

### 对局 `/api/match`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/start` | 初始化对局状态（Redis），广播对局详情 |
| GET | `/state` | 获取当前对局状态 |
| POST | `/roll_dice` | 掷骰子 |
| POST | `/select_score` | 选择计分项 |
| GET | `/final_score` | 获取对局最终成绩 |

### 排行榜 `/api/ranking`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/total` | 总排行榜 |
| GET | `/daily` | 每日排行榜 |

## WebSocket 接口

### 房间频道 `/ws/room/{room_id}?token=xxx`

连接后自动加入房间频道，接收以下事件：

| 事件类型 | 方向 | 说明 |
|---------|------|------|
| `room_sync` | S→C | 连接时推送当前房间完整玩家列表 |
| `player_join` | S→C | 有玩家加入房间 |
| `player_leave` | S→C | 有玩家离开房间 |
| `player_ready` | S→C | 玩家准备状态变更 |
| `match_started` | S→C | 对局创建，推送 `match_id` |
| `room_dissolve` | S→C | 房间已解散 |
| `player_disconnect` | S→C | 有玩家断开连接 |

### 对局频道 `/ws/match/{match_id}?token=xxx`

连接后自动加入对局频道，接收以下事件：

| 事件类型 | 方向 | 说明 |
|---------|------|------|
| `match_ready` | S→C | 对局初始化完成，推送完整对局信息 |
| `dice_rolled` | S→C | 有玩家掷骰，推送骰子结果 |
| `score_selected` | S→C | 有玩家选分，推送得分详情 |
| `your_turn` | S→C | 轮到当前玩家操作 |
| `game_ended` | S→C | 游戏结束，推送最终排名 |
| `player_disconnect` | S→C | 有玩家断开连接 |
| `ping` | C→S | 客户端心跳 |
| `pong` | S→C | 服务端心跳响应 |
| `player_action` | C→S | 客户端同步操作，转发给其他玩家 |

## 游戏流程

```
创建房间 → 分享房间号 → 等待玩家加入 → 所有人准备
    ↓
房主触发开始 → 创建对局 → 广播 match_id
    ↓
前端调用 /start 初始化对局 → 连接对局 WebSocket
    ↓
随机起始玩家 → 掷骰（最多3次）→ 选择计分项 → 下一玩家
    ↓
重复 13 轮 → 计算总分（含上半部分奖励）→ 排名 → 游戏结束
```

## 游戏规则（Yahtzee）

- 每局 13 轮，每轮每位玩家最多掷 3 次骰子
- 第一次掷出 5 颗骰子，后续可选择保留部分骰子重掷其余
- 掷骰后从 13 个计分项中选择一个计分（每个计分项只能用一次）
- 上半部分（ones ~ sixes）总分 ≥ 63 额外奖励 35 分
- Yahtzee（5 颗相同）首次得 50 分，再次得 100 分奖励
- 13 轮结束后总分最高者获胜

### 计分项

| 计分项 | 规则 |
|--------|------|
| ones ~ sixes | 对应点数的骰子值之和 |
| three_of_a_kind | 3 颗相同，全部骰子之和 |
| four_of_a_kind | 4 颗相同，全部骰子之和 |
| full_house | 3+2 组合，固定 25 分 |
| small_straight | 4 个连续数字，固定 30 分 |
| large_straight | 5 个连续数字，固定 40 分 |
| yahtzee | 5 颗相同，固定 50 分 |
| chance | 任意组合，全部骰子之和 |
