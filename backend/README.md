# CatTrace Agent Backend

当前后端提供本地 SQLite 认证与角色管理，以及 YOLO 猫咪识别接口，用于前端登录、注册、管理员管理和上传图片识别。

## 运行

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python main.py
```

服务默认运行在：

```text
http://localhost:8888
```

## 已提供接口

- `GET /api/health`：健康检查。
- `POST /api/auth/register`：普通用户注册。
- `POST /api/auth/login`：用户/管理员/总管理员登录。
- `POST /api/auth/logout`：登出并清除 Cookie。
- `GET /api/auth/me`：获取当前登录用户信息。
- `PUT /api/auth/profile`：更新个人资料。
- `PUT /api/auth/password`：修改密码。
- `GET /api/auth/users`：总管理员查看用户列表。
- `GET /api/auth/admins`：总管理员查看管理员列表。
- `POST /api/auth/admins`：总管理员创建管理员账号。
- `PUT /api/auth/users/{user_id}/role`：总管理员调整用户角色。
- `POST /api/recognition/analyze`：上传一张或多张图片，使用 `models/cat_breeds/best.pt` 执行 YOLO 识别。

默认种子账号：

- 总管理员兼容账号：`superadmin` / `admin123`
- 总管理员手机号账号：`13900000000` / `admin123`
- 管理员兼容账号：`admin` / `admin123`
- 管理员手机号账号：`13800000000` / `admin123`

新注册普通用户必须使用手机号作为账号。总管理员创建的新管理员也必须使用手机号作为账号。

本地 SQLite 数据库默认位于 `backend/data/cattrace.db`，该目录已被 `.gitignore` 忽略。

`POST /api/recognition/analyze` 请求字段：

- `files`: 图片文件数组，表单字段名固定为 `files`。
- `conf_threshold`: 可选，默认 `0.25`。

响应会返回：

- `candidates`: Top 3 YOLO 候选结果。
- `analysis`: 前端分析卡片需要的摘要信息。
- `uploadedImages`: 后端保存的上传图片 URL。
- `detectedCount`: 检测到的目标数量。
- `elapsedMs`: 推理耗时。

## 当前不包含

- 猫咪个体身份匹配。
- 出现记录保存。
- 领养业务接口。

训练脚本、评估脚本、训练报告和评估结果已移动到项目根目录的 `yolo_training_artifacts/`。
