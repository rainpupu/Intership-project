# CatTrace Agent 项目交接文档

本文档用于新工作 Agent 接手当前项目。请先完整阅读本文，再进行任何代码修改、提交或合并。

## 1. 项目定位

项目名称：CatTrace Agent

项目目标：建设一个面向校园或社区流浪猫管理与领养场景的平台。系统通过 YOLO 视觉识别和后续智能体能力，为流浪猫建立数字档案，支持识别记录、猫咪图鉴、领养入口、用户上传识别、管理员审核管理和 AI 助手入口。

当前项目不是一次性静态 Demo，而是一个需要继续迭代的正式前后端项目。所有改动都应优先保证结构清晰、职责分层、可继续扩展。

核心业务设想：

- 用户端展示猫咪图鉴、猫咪详情、领养入口、AI 助手、个人信息、我的识别。
- 普通用户可以注册、登录、补全资料、上传图片进行识别，但只能看到自己上传产生的相关数据。
- 普通管理员只能登录自己的账号，后续主要负责审核、猫咪档案维护、识别结果确认等。
- 高级管理员可以查看所有用户和管理员信息，并创建新管理员账号、赋予管理员职责。
- YOLO 当前只做识别最小闭环，不接数据库持久化识别记录。
- 后续数据库需要逐步承接用户、猫咪档案、识别记录、领养申请、管理员审核流程。

## 2. 当前目录结构

项目根目录：

```text
C:\Users\15510\Desktop\Intership-project
```

主要目录：

```text
backend/                    FastAPI 后端，包含 YOLO 识别接口、认证接口、数据库初始化
frontend/                   Vue 3 前端
yolo_training_artifacts/    已独立出去的 YOLO 训练、评估、报告等非运行必要内容
.gitignore                  忽略本地产物、虚拟环境、构建产物等
HANDOFF.md                  本交接文档
```

不要把训练脚本、评估报告等重新混回 `backend/` 或 `frontend/`。它们和项目运行落地无关，应继续放在 `yolo_training_artifacts/` 这类独立路径下。

## 3. Git 和分支状态

当前主线已经整理为最小可运行版本。

- 当前分支：`main`
- `main` 已被替换为最小可运行版本，并已推送到 GitHub。
- `main` / `origin/main` 当前基础提交：`af4ab34 feat: complete phone auth and role management`
- `minimal-runnable-yolo` 分支也曾作为最小可运行版本分支使用。

当前交接时工作区状态：

```text
## main...origin/main
 M frontend/src/views/user/Home.vue
```

这唯一未提交改动是：删除首页 Hero 区域三个按钮：

- 查看猫咪图鉴
- 进入管理端
- AI 助手

该改动已经运行过：

```powershell
cd C:\Users\15510\Desktop\Intership-project\frontend
npm.cmd run build
```

构建通过。构建过程中只有依赖注释和 chunk 体积警告，不影响运行。

如果用户确认该修改要入库，可执行：

```powershell
cd C:\Users\15510\Desktop\Intership-project
git add frontend/src/views/user/Home.vue HANDOFF.md
git commit -m "chore: update handoff and home actions"
git push origin main
```

如果只提交交接文档，则不要顺手提交 `Home.vue`，除非用户确认。

## 4. 技术栈

前端：

- Vue 3
- TypeScript
- Vite
- Vue Router 4
- Pinia
- Element Plus
- Axios
- ECharts
- SCSS

后端：

- FastAPI
- SQLAlchemy
- SQLite 当前开发默认数据库
- JWT 登录态
- bcrypt 密码哈希
- YOLO 推理最小服务

当前阶段重点是最小可运行闭环，不要过度设计复杂平台能力。

## 5. 运行方式

### 5.1 前端

```powershell
cd C:\Users\15510\Desktop\Intership-project\frontend
npm install
npm.cmd run dev
```

注意：当前 Windows PowerShell 可能禁止运行 `npm.ps1`，因此优先使用 `npm.cmd`，不要直接使用 `npm`。

构建验证：

```powershell
cd C:\Users\15510\Desktop\Intership-project\frontend
npm.cmd run build
```

### 5.2 后端

```powershell
cd C:\Users\15510\Desktop\Intership-project\backend
.\.venv\Scripts\Activate.ps1
uvicorn main:app --reload
```

如果虚拟环境不存在，优先使用 `uv` 创建和安装依赖：

```powershell
cd C:\Users\15510\Desktop\Intership-project\backend
uv venv
.\.venv\Scripts\Activate.ps1
uv pip install -r requirements.txt
```

不要把 `.venv` 提交到 Git。

## 6. 默认账号

后端启动时会初始化默认角色和默认账号。

高级管理员：

```text
手机号：13900000000
密码：admin123
角色：super_admin
```

普通管理员：

```text
手机号：13800000000
密码：admin123
角色：admin
```

普通用户可通过前端注册流程创建。注册必须使用手机号作为账号。

## 7. 当前已实现功能

### 7.1 前端框架

已完成：

- Vue 3 + TypeScript + Vite 工程结构
- Vue Router 路由分层
- Pinia 状态基础
- Element Plus UI
- Axios 请求封装
- SCSS 全局样式
- 用户端 Layout
- 管理端 Layout
- 首页
- 猫咪图鉴
- 猫咪详情
- AI 助手静态/悬浮入口相关基础
- 用户个人信息页面
- 用户识别页面
- 管理端 Dashboard
- 管理端 Recognition
- 管理端猫咪管理占位
- 高级管理员账号管理页面

### 7.2 YOLO 识别链路

已完成最小可运行链路：

- 前端上传图片。
- 后端 FastAPI 接收图片。
- 后端调用本地 YOLO 模型识别。
- 前端展示识别结果。
- 候选结果当前只显示置信度最高的一条。
- 候选结果左侧图使用 YOLO 识别后带绿色框的结果图。
- 图片上传后支持查看原图预览。
- 上传框布局已调整：上传后记录替代大加号，继续上传入口缩小放在操作区。

当前限制：

- 识别记录尚未写入数据库。
- 用户只能看到自己上传数据的持久化逻辑尚未完整落库。
- 识别结果确认、创建猫档案、关联已有猫档案仍是后续任务。

### 7.3 用户和管理员认证链路

已完成：

- 用户手机号注册。
- 注册时设置密码。
- 注册成功后跳转个人资料填写页面。
- 个人资料填写必填：昵称、邮箱、手机号自动填充、身份说明。
- 身份说明已经改为下拉选择，不能随意输入文字。
- 注册资料保存后跳转首页。
- 用户登录输入账号和密码。
- 登录成功后跳转首页。
- 手机号已注册但密码错误时提示密码错误。
- 手机号未注册时提示去注册。
- 管理员登录。
- 普通管理员只能进入自己的管理员能力范围。
- 高级管理员可以查看所有用户和管理员信息。
- 高级管理员可以创建管理员账号并赋予管理员角色。

当前仍需继续验证和完善：

- 登录态过期后的全局处理。
- 刷新页面后的用户状态恢复细节。
- 权限不足页面或统一错误页。
- 普通管理员与高级管理员在更多管理端页面上的能力边界。

## 8. 关键文件说明

### 8.1 前端关键文件

```text
frontend/src/api/request.ts
```

Axios 封装。当前会携带 token 和 cookie。后续接后端新接口优先从这里统一处理 baseURL、认证头、错误拦截。

```text
frontend/src/api/auth.ts
```

前端认证 API。当前已对接后端真实认证接口，不再是 mock。

```text
frontend/src/types/user.ts
```

用户、角色、注册登录 payload 类型。

```text
frontend/src/router/routes.ts
frontend/src/router/index.ts
```

路由和权限拦截。新增页面或改权限时优先在这里维护。

```text
frontend/src/views/auth/Login.vue
frontend/src/views/auth/Register.vue
```

登录和注册页面。

```text
frontend/src/views/user/Profile.vue
```

个人资料填写和编辑页面。注册后 setup 模式会走这里。

```text
frontend/src/views/user/UserRecognition.vue
```

普通用户识别页面。

```text
frontend/src/views/admin/UserManage.vue
```

高级管理员账号管理页面。

```text
frontend/src/views/user/Home.vue
```

首页。当前有未提交修改：删除 Hero 三个按钮。

### 8.2 后端关键文件

```text
backend/main.py
```

FastAPI 入口，挂载认证和识别相关路由，启动时初始化数据库。

```text
backend/app/api/auth.py
```

认证接口，包括注册、登录、退出、当前用户、资料更新、管理员创建、用户列表等。

```text
backend/app/services/user_service.py
```

用户业务逻辑，包括手机号注册、密码验证、profile 更新、角色处理。

```text
backend/app/entity/db_models.py
```

SQLAlchemy 模型：User、Role、UserRole。

```text
backend/app/entity/schemas/auth.py
```

认证相关 Pydantic schema。

```text
backend/app/database/session.py
```

数据库连接和 Session 管理。

```text
backend/app/database/seed.py
```

默认角色和默认管理员账号初始化。

```text
backend/app/config/settings.py
```

后端配置项，包括数据库路径、JWT、CORS 等。

## 9. 数据库现状

当前开发默认使用 SQLite。

数据库文件通常位于：

```text
backend/data/cattrace.db
```

数据库文件不应提交到 Git。

之前已清理过旧用户数据，只保留默认管理员种子账号。后续如果需要重新清空开发数据，应谨慎操作，优先确认用户是否需要保留测试账号。

## 10. 不要提交的内容

必须避免提交：

```text
backend/.venv/
frontend/node_modules/
frontend/dist/
backend/data/*.db
__pycache__/
frontend/tsconfig.tsbuildinfo
backend/app/**/__pycache__/
*.pyc
```

提交前必须检查：

```powershell
git status --short
git diff --cached --name-only
```

如果看到虚拟环境、数据库、构建产物、缓存文件，先移除暂存。

## 11. 开发准则

### 11.1 总体准则

- 不要把所有逻辑堆到单个 Vue 文件或单个后端文件中。
- 前端 API、页面、组件、类型、状态要分层。
- 后端 API、service、schema、model 要分层。
- 不要因为当前是最小版本就写临时不可扩展代码。
- 不要随意重构无关文件。
- 每次修改后优先运行能覆盖本次改动的最小验证。
- 保留现有风格和目录结构。

### 11.2 前端准则

- 使用 Vue 3 Composition API。
- 组件 props 类型要明确。
- 页面负责组合组件，不直接塞大量可复用逻辑。
- API 调用集中放在 `src/api/`。
- 类型放在 `src/types/`。
- 样式优先使用已有 SCSS 变量。
- 视觉风格保持温暖、现代、猫咪主题，不要改成冷冰冰后台风格。
- 管理端可以更理性，但仍要保持 CatTrace 品牌感。
- 用户端按钮、卡片、列表等交互应简洁，不要过度装饰。

### 11.3 后端准则

- 路由层只做请求响应编排。
- 业务逻辑放 service。
- 数据结构放 schema/model。
- 密码必须哈希，不要明文保存。
- 认证错误要返回可被前端区分的 code，例如 `INVALID_PASSWORD`、`PHONE_NOT_REGISTERED`。
- 后续新增数据库表时要考虑迁移方案。目前尚未接入 Alembic，如引入需统一设计。

### 11.4 Git 准则

- 用户没有要求时，不要随便强推。
- 提交前检查暂存范围。
- 如果有用户未提交改动，不要覆盖或回滚。
- 如果需要覆盖分支历史，必须先获得用户明确确认。
- 当前 `main` 已经是项目主线，不要再恢复旧 main 内容。

## 12. 已知问题和注意事项

1. PowerShell 直接运行 `npm` 可能失败，应使用 `npm.cmd`。
2. `npm.cmd run build` 可能生成 `frontend/tsconfig.tsbuildinfo`，构建后如未被忽略或显示未跟踪，应删除，不要提交。
3. Vite 构建有 chunk 体积警告，主要来自 Element Plus/ECharts，暂时不影响运行。
4. 当前 YOLO 结果没有完整数据库持久化。
5. 当前识别和猫咪档案的正式关联逻辑还未完成。
6. 用户上传记录的“只能看到自己数据”需要在数据库表设计后完整落实。
7. 首页已经有悬浮猫 AI 助手方向的改造，首页 Hero 的 AI 助手入口框已逐步移除。
8. 当前桌宠猫咪是轻量实现，不要再加入复杂骨骼动画或重型 3D，除非用户明确要求。

## 13. 下一步建议优先级

建议后续按以下顺序推进：

1. 提交当前 `Home.vue` 按钮删除改动和本交接文档。
2. 完整手动测试用户注册、资料补全、登录、退出、再次登录。
3. 完整测试普通管理员登录和高级管理员登录。
4. 测试高级管理员创建新管理员、列表刷新、权限边界。
5. 设计识别记录数据库表：
   - 上传用户
   - 原图路径
   - YOLO 标注图路径
   - 检测类别
   - 置信度
   - bbox
   - 创建时间
   - 审核状态
6. 将用户识别结果写入数据库，并让普通用户只能查看自己的识别记录。
7. 增加管理员识别记录审核页。
8. 设计猫咪档案表和识别结果关联已有猫/创建新猫档案流程。
9. 逐步替换前端 mock 猫咪数据为后端接口。
10. 后续再考虑领养申请、云领养、AI 助手真实接口。

## 14. 新 Agent 接手后的第一步

建议新 Agent 进入项目后先运行：

```powershell
cd C:\Users\15510\Desktop\Intership-project
git status --short --branch
git log -1 --oneline
```

然后确认：

- 当前是否仍在 `main`。
- 是否只有 `frontend/src/views/user/Home.vue` 和 `HANDOFF.md` 改动。
- 用户是否希望提交这两个文件。

如果继续开发，不要一上来大范围重构。先根据用户下一条明确需求做小步修改、验证、提交。
