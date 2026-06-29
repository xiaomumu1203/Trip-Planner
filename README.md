# Trip-Planner 智能旅行助手

基于 FastAPI + Vue3 的 AI 旅行规划系统。用户输入目的地、日期和偏好，后端通过多智能体架构调度 LLM 自主调用高德地图 API 获取数据，整合生成完整的每日行程计划。

## 功能

- AI 景点推荐 — LLM 根据偏好自动搜索并筛选景点
- 天气预报 — 自动查询旅行期间的天气预报
- 酒店推荐 — 根据住宿偏好推荐酒店
- 每日行程 — LLM 整合景点+天气+酒店，生成完整每日计划
- 预算估算 — 自动汇总景点门票、酒店、餐饮、交通费用
- 景点图片 — 自动搜索景点配图

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI (Python 3.12) |
| 数据校验 | Pydantic v2 |
| LLM 集成 | OpenAI SDK（兼容 DeepSeek / 通义千问等） |
| 外部 API | 高德地图 POI/天气/路线 API, Unsplash 图片 API |
| 前端 | Vue 3 + TypeScript + Vite + Ant Design Vue |
| HTTP 客户端 | httpx |
| 运行环境 | Uvicorn |

## 项目结构

```
backend/
├── run.py                         # 启动入口
├── app/
│   ├── main.py                    # FastAPI 应用、CORS、路由挂载
│   ├── config.py                  # 配置管理（.env + pydantic-settings）
│   ├── api/routes/
│   │   ├── trip.py                # 旅行规划接口（POST /api/trip/plan）
│   │   ├── map.py                 # 高德地图查询接口（POI/天气/路线）
│   │   └── poi.py                 # POI 详情 + 景点图片接口
│   ├── agents/
│   │   └── trip_planner_agent.py  # 多智能体核心（4个Agent协作）
│   ├── services/
│   │   ├── llm_service.py         # LLM 客户端 + ToolAgent 框架
│   │   ├── amap_service.py        # 高德地图 API 封装
│   │   └── unsplash_service.py    # Unsplash 图片 API 封装
│   ├── tools/
│   │   └── tool.py                # Function Calling Schema + 工具映射
│   └── models/
│       └── schemas.py             # Pydantic 数据模型
│
frontend/
├── src/
│   ├── App.vue                    # 根组件
│   ├── main.ts                    # 入口
│   ├── views/
│   │   ├── Home.vue               # 首页（表单）
│   │   └── Result.vue             # 结果页（行程展示）
│   ├── services/api.ts            # API 调用封装
│   └── types/index.ts             # TypeScript 类型定义
├── index.html
├── vite.config.ts
└── package.json
```

## 快速开始

### 1. 克隆项目

```bash
git clone <repo-url>
cd trip-planner
```

### 2. 后端配置

```bash
cd backend

# 创建虚拟环境
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
# source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
# 复制以下内容创建 .env 文件
```

在 `backend/.env` 中配置：

```env
# 高德地图 API（必填 - 用于景点/天气/酒店搜索）
AMAP_API_KEY=your_amap_api_key

# LLM 配置
OPENAI_API_KEY=your_deepseek_api_key
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_MODEL=deepseek-chat

# Unsplash（可选 - 用于景点图片，不配置则无配图）
UNSPLASH_ACCESS_KEY=your_unsplash_access_key
```

### 3. 启动后端

```bash
cd backend
python run.py
```

服务启动在 http://localhost:8000，API 文档访问 http://localhost:8000/docs

### 4. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端开发服务器启动在 http://localhost:5173

## 多智能体架构

系统由 4 个 Agent 协作完成旅行规划：

```
用户输入（城市 + 日期 + 偏好）
        │
        ▼
┌──────────────────────────────────────┐
│  步骤 1-3：并行执行                     │
│                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────┐ │
│  │ 景点搜索  │  │ 天气查询  │  │ 酒店  │ │
│  │  Agent   │  │  Agent   │  │ Agent│ │
│  └────┬─────┘  └────┬─────┘  └──┬───┘ │
│       │             │           │     │
│   调高德POI      调高德天气    调高德POI  │
│       │             │           │     │
└───────┼─────────────┼───────────┼─────┘
        │             │           │
        ▼             ▼           ▼
┌──────────────────────────────────────┐
│  步骤 4：行程规划 Agent                │
│  LLM 整合所有数据 → 输出完整 JSON       │
└──────────────────────────────────────┘
        │
        ▼
   返回前端渲染
```

- **景点搜索 Agent** — LLM 自主决定调用 `search_poi` 工具搜索景点 POI
- **天气查询 Agent** — LLM 自主决定调用 `get_weather` 工具查询天气预报
- **酒店推荐 Agent** — LLM 自主决定调用 `search_poi` 工具搜索酒店 POI
- **行程规划 Agent** — 纯 LLM 调用，将前三步数据整合为结构化行程

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/trip/plan | 生成旅行计划 |
| GET  | /api/map/poi | 搜索 POI |
| GET  | /api/map/weather | 查询天气 |
| GET  | /api/map/route | 路线规划 |
| GET  | /api/poi/detail | POI 详情 |
| GET  | /api/poi/photo | 景点图片 |
| GET  | /health | 健康检查 |

## 配置说明

系统通过 `backend/.env` 文件配置，主要配置项：

| 配置项 | 必填 | 说明 |
|--------|------|------|
| AMAP_API_KEY | 是 | 高德地图 Web 服务 API Key |
| OPENAI_API_KEY | 是 | LLM API Key（DeepSeek） |
| OPENAI_BASE_URL | 是 | LLM API 地址 |
| OPENAI_MODEL | 是 | 模型名称 |
| UNSPLASH_ACCESS_KEY | 否 | Unsplash API Key（不配则无景点配图） |

## 开发

```bash
# 后端热重载（默认已开启 reload=True）
cd backend && python run.py

# 前端开发模式
cd frontend && npm run dev
```

## License

MIT
