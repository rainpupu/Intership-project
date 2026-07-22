# CatTrace Agent

CatTrace Agent 是一个面向校园流浪猫管理场景的智能档案平台。系统通过图像识别、个体特征匹配、线索审核和数字档案维护，将分散的猫咪发现记录沉淀为可持续更新的结构化档案，并支持云领养、管理员运营和账号权限管理。

## 项目概览

平台围绕“发现猫咪、识别猫咪、确认身份、维护档案、持续关怀”的业务链路设计，覆盖普通用户、管理员和总管理员三类角色。

- 普通用户可以注册登录、上传猫咪图片、查看识别结果、提交校园猫线索、浏览猫咪图鉴、查看猫咪详情并参与云领养。
- 管理员可以处理识别任务、确认已有猫匹配、创建新猫档案、审核用户线索、维护猫咪档案和查看云领养订单。
- 总管理员可以管理平台账号、创建管理员、调整角色并删除账号。

## 核心功能

### 用户端

- 手机号注册与登录
- 首页数据概览与推荐猫咪
- 猫咪图鉴与猫咪详情页
- 猫咪历史出现时间线，包含时间、地点、健康状态和心情状态
- 图片上传识别与个人识别记录
- 校园猫线索提交，支持填写拍摄地点、拍摄时间和补充说明
- 云领养支持，可选择食物、玩具、健康用品等虚拟物资
- AI 助手对话，支持猫咪查询、状态咨询和领养建议

### 管理端

- 数据概览：猫咪数量、识别任务、待跟进事件、开放领养等
- 管理端识别任务：
  - 上传图片并调用识别模型
  - 匹配已有猫时，管理员必须填写发现地点和发现时间后才能登记到档案
  - 未达到匹配阈值时按新猫处理，不展示低置信度的最近档案干扰判断
  - 创建新猫档案时必须填写发现地点和发现时间
- 线索审核：
  - 查看用户提交的校园猫线索
  - 将线索确认到已有猫档案
  - 将疑似新猫线索创建为新档案
- 猫咪档案管理：
  - 新增、编辑、删除猫咪档案
  - 查看审核记录
  - 重点关注与批量标记
- 云领养订单管理：
  - 查看用户支持记录
  - 汇总订单数量、支持金额和物资数量
- 账号管理：
  - 创建管理员账号
  - 调整普通用户与管理员角色
  - 总管理员删除账号

## 技术栈

### 前端

- Vue 3
- TypeScript
- Vite
- Pinia
- Vue Router
- Element Plus
- ECharts
- Sass

### 后端

- FastAPI
- SQLAlchemy
- SQLite / PostgreSQL
- JWT 认证
- YOLO / Ultralytics
- PyTorch / TorchVision
- LangGraph / LangChain
- OpenAI API 兼容接口

## 目录结构

```text
.
├── backend/                  # FastAPI 后端服务
│   ├── app/
│   │   ├── api/              # HTTP API 路由
│   │   ├── config/           # 配置管理
│   │   ├── database/         # 数据库会话、初始化与运行时迁移
│   │   ├── entity/           # ORM 模型与 Pydantic Schema
│   │   ├── services/         # 业务服务、识别流程与智能体能力
│   │   └── storage/          # 存储相关封装
│   ├── main.py               # 后端入口
│   └── requirements.txt      # Python 依赖
├── frontend/                 # Vue 前端应用
│   ├── public/
│   ├── src/
│   │   ├── api/              # 前端 API 封装
│   │   ├── components/       # 通用组件与业务组件
│   │   ├── composables/      # 组合式业务流程
│   │   ├── layouts/          # 用户端与管理端布局
│   │   ├── router/           # 路由配置
│   │   ├── stores/           # Pinia 状态管理
│   │   ├── types/            # TypeScript 类型定义
│   │   └── views/            # 页面视图
│   ├── package.json
│   └── vite.config.ts
├── knowledge/                # 知识库资料
├── tests/                    # 后端测试
├── docker-compose.yml        # PostgreSQL、Redis、MinIO 基础服务
└── README.md
```

## 本地运行

### 1. 启动基础服务

如需使用 PostgreSQL、Redis 或 MinIO，可先启动基础服务：

```bash
docker compose up -d
```

默认开发配置可使用 SQLite，本地首次启动后端时会自动初始化数据库表和基础数据。

### 2. 启动后端

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8888 --reload
```

后端服务默认地址：

```text
http://localhost:8888
```

接口文档地址：

```text
http://localhost:8888/docs
```

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端默认地址：

```text
http://localhost:5173
```

## 环境变量

后端支持通过 `backend/.env` 配置运行参数。实际部署时不要提交 `.env` 文件。

常用配置项：

```text
DATABASE_URL=sqlite:///./data/cattrace.db
JWT_SECRET_KEY=replace-with-a-secure-secret
OPENAI_API_KEY=replace-with-your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
```

前端可通过环境变量配置 API 地址：

```text
VITE_API_BASE_URL=http://localhost:8888/api
```

如果不配置，前端默认使用 `/api` 作为请求前缀。

## 测试与构建

### 前端构建

```bash
cd frontend
npm run build
```

### 后端测试

```bash
python -m pytest
```

## 数据与模型文件说明

以下内容属于本地运行产物或大体积资源，不应提交到源码仓库：

```text
.env
backend/.venv/
backend/data/
backend/logs/
backend/models/
backend/static/
frontend/node_modules/
frontend/dist/
*.db
*.pt
*.pyc
```

模型权重、训练数据和运行数据库应通过部署环境、对象存储或单独的数据交付流程管理。

## 权限模型

系统内置三类角色：

- 普通用户：上传识别图片、提交校园线索、查看个人记录、浏览猫咪档案、参与云领养。
- 管理员：处理识别任务、审核线索、维护猫咪档案、查看云领养订单。
- 总管理员：具备管理员能力，并可创建管理员、调整角色和删除账号。

## 项目状态

当前版本已完成用户端、管理端和总管理员端的主要业务闭环，包括猫咪识别、线索审核、档案维护、云领养订单和账号管理能力。后续可继续扩展模型训练管理、移动端适配、通知系统、支付对接和更细粒度的数据权限控制。
