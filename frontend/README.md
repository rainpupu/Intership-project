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
- `/profile` 个人信息页
- `/recognition` 普通用户识别与个人记录页
- `/admin/dashboard` 管理端首页
- `/admin/recognition` 猫咪识别页面
- `/admin/cats` 猫咪管理占位页

## 结构说明

- `src/api`：Axios 实例与 Mock API 封装，后续可替换为 FastAPI 请求。
- `src/components`：按业务域拆分的可复用组件。
- `src/composables`：页面复用的组合式业务逻辑，例如识别流程。
- `src/layouts`：用户端与管理端布局。
- `src/mock`：当前阶段的 Mock 数据源。
- `src/router`：路由定义与实例。
- `src/stores`：Pinia 全局状态。
- `src/types`：核心业务类型。
- `src/assets/styles`：SCSS 变量、混入、重置与全局样式。

## 登录说明

当前认证为 Mock 实现：

- 使用 `user / 任意密码` 登录为普通用户，可访问 `/recognition`，只查看自己的识别记录。
- 使用 `admin / 任意密码` 登录为普通管理员，可访问 `/admin/*`。
- 使用 `superadmin / 任意密码` 登录为总管理员，可访问 `/admin/*`，并预留全平台账号管理接口。

后续接入 FastAPI 时，可替换 `src/api/auth.ts` 和 `src/api/recognition.ts` 内部实现，页面和状态层无需大改。

## 账号与权限接口预留

`src/api/auth.ts` 已预留以下接口：

- `login(payload)`：用户、普通管理员、总管理员登录。
- `register(payload)`：普通用户注册并登录，不创建管理员账号。
- `getCurrentUser(token)`：根据 token 获取当前账号资料。
- `updateUserProfile(profile, payload)`：更新当前用户资料。
- `getUserList(query)`：总管理员查询用户和管理员账号列表。
- `getAdminList()`：总管理员查询普通管理员列表。
- `createAdmin(payload)`：总管理员创建新管理员账号。
- `updateUserRole(payload)`：总管理员将普通用户设为管理员，或撤回为普通用户。

角色类型定义在 `src/types/user.ts`：

- `user`：普通用户，可注册、登录、上传识别图片，只查看自己的识别记录。
- `admin`：普通管理员，只能通过管理员账号登录，进入管理端处理平台业务。
- `super_admin`：总管理员，可查看用户和管理员账号信息，并创建或分配管理员职责。

## 已优化项

- 登录和注册页会在已登录时自动跳转到对应角色页面。
- 普通用户访问管理端会提示无权限并回到个人识别页。
- `/profile` 隐藏顶部导航，并通过记录来源路径返回进入前页面。
- 用户资料支持头像预览、头像 URL 校验、默认头像兜底和本地持久化。
- 猫咪图鉴、详情、Dashboard、识别记录增加 loading / error / empty 状态。
- 用户端和管理端识别流程复用 `useRecognitionFlow`，便于后续接入真实识别接口。
- Vite 已配置基础 manualChunks，ECharts 改为按需注册。
