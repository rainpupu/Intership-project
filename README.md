# VisAgent

基于 YOLOv11 的遥感目标检测智能体平台，提供图像检测、模型训练、智能对话等一站式 AI 检测服务。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI + Uvicorn |
| 前端框架 | Vue 3 + Vite + Element Plus |
| 数据库 | PostgreSQL（pgvector） |
| 缓存 | Redis |
| 对象存储 | MinIO |
| 包管理 | uv（Python）/ bun（Node.js） |
| 容器化 | Docker Compose |

## 快速开始

### 1. 环境要求

- Python 3.11 ~ 3.14
- Node.js（推荐使用 bun）
- Docker 与 Docker Compose

### 2. 启动基础设施

```bash
docker compose up -d
```

启动 PostgreSQL、Redis、MinIO 三个基础服务。

### 3. 启动后端

```bash
cd backend

# 复制环境变量模板并编辑
cp .env.example .env

# 安装依赖
uv sync --group dev

# 启动开发服务器（端口 8888）
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8888
```

API 文档：http://localhost:8888/docs

### 4. 启动前端

```bash
cd frontend

# 安装依赖
bun install

# 启动开发服务器（端口 3000）
bun run dev
```

前端自动将 `/api` 请求代理到后端 `http://localhost:8888`。

访问：http://localhost:3000

## 项目结构

```
visagent/
├── docker-compose.yml        # 基础设施编排
├── backend/
│   ├── app/
│   │   ├── api/              # API 路由层
│   │   │   └── auth.py       # 认证接口（注册/登录/当前用户）
│   │   ├── config/           # 全局配置（pydantic-settings）
│   │   │   └── settings.py
│   │   ├── core/             # 核心工具
│   │   │   └── security.py   # 密码哈希 + JWT Token
│   │   ├── database/         # 数据库
│   │   │   └── session.py    # SQLAlchemy 会话管理
│   │   ├── entity/           # 数据实体
│   │   │   ├── db_models.py  # ORM 模型（12 张表）
│   │   │   └── schemas.py    # Pydantic Schema
│   │   ├── services/         # 业务服务层
│   │   │   └── user_service.py
│   │   └── storage/          # 对象存储
│   │       └── minio_client.py
│   ├── alembic/              # 数据库迁移
│   ├── tests/                # 测试套件（88 个用例）
│   ├── main.py               # 应用入口
│   └── pyproject.toml
└── frontend/
    └── src/
        ├── api/              # API 请求封装
        ├── assets/styles/    # SCSS 样式系统
        ├── components/layout/ # 布局组件
        ├── router/           # Vue Router 路由
        ├── stores/           # Pinia 状态管理
        ├── utils/            # 工具函数（请求/流式/Markdown）
        └── views/            # 页面视图
```

## 数据库模型

系统设计了 12 张数据表，覆盖五大业务域：

**用户权限（RBAC）**：`users`、`roles`、`permissions`、`user_roles`、`role_permissions`

**检测业务**：`detection_scenes`（检测场景配置）、`detection_tasks`（检测任务）、`detection_results`（检测结果）

**模型管理**：`training_tasks`（训练任务）、`training_metrics`（训练指标）、`model_versions`（模型版本）

**智能体对话**：`chat_sessions`（对话会话）、`chat_messages`（对话消息）

**系统运维**：`operation_logs`（操作审计日志）

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register` | 用户注册 |
| POST | `/api/auth/login` | 用户登录，返回 JWT Token |
| GET | `/api/auth/me` | 获取当前用户信息（需认证） |
| GET | `/api/health` | 服务健康检查 |
| GET | `/api/health/database` | 数据库连接检查 |
| GET | `/api/health/redis` | Redis 连接检查 |
| GET | `/api/health/minio` | MinIO 连接检查 |

## 开发指南

### 后端

```bash
cd backend

# 代码检查
uv run ruff check app/

# 代码格式化
uv run ruff format app/

# 运行测试
uv run pytest
```

### 前端

```bash
cd frontend

# 构建生产版本
bun run build

# 预览生产构建
bun run preview
```

## 许可证

本项目采用 [木兰宽松许可证 v2](http://license.coscl.org.cn/MulanPSL2)。
