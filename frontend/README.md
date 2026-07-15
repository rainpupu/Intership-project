# CatTrace Agent Frontend

基于 Vue 3、TypeScript、Vite、Vue Router、Pinia、Element Plus、Axios、ECharts 与 SCSS 搭建的 CatTrace Agent 前端工程。

当前阶段只实现前端框架、基础路由、Mock API、用户端基础页面与管理端识别流程骨架，不包含真实后端、真实 AI 接口或真实文件上传。

## 运行

```bash
cd frontend
npm install
npm run dev
```

## 已实现页面

- `/` 首页
- `/cats` 猫咪图鉴
- `/cats/:id` 猫咪详情
- `/chat` AI 助手静态聊天页
- `/login` 登录页
- `/register` 注册页
- `/recognition` 普通用户识别与个人记录页
- `/admin/dashboard` 管理端首页
- `/admin/recognition` 猫咪识别页面
- `/admin/cats` 猫咪管理占位页

## 结构说明

- `src/api`：Axios 实例与 Mock API 封装，后续可替换为 FastAPI 请求。
- `src/components`：按业务域拆分的可复用组件。
- `src/layouts`：用户端与管理端布局。
- `src/router`：路由定义与实例。
- `src/stores`：Pinia 全局状态。
- `src/types`：核心业务类型。
- `src/assets/styles`：SCSS 变量、混入、重置与全局样式。

## 登录说明

当前认证为 Mock 实现：

- 使用 `user / 任意密码` 登录为普通用户，可访问 `/recognition`，只查看自己的识别记录。
- 使用 `admin / 任意密码` 登录为管理员，可访问 `/admin/*`，查看全平台数据。

后续接入 FastAPI 时，可替换 `src/api/auth.ts` 和 `src/api/recognition.ts` 内部实现，页面和状态层无需大改。
