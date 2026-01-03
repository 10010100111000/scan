## 使用 Vben Admin 重新初始化前端

我们已移除旧的自建前端代码（Vue + Ant Design Vue）。请使用 Vben Admin 官方模板在 `frontend/` 目录重建项目，以获得登录/布局/权限等现成能力。

### 初始化步骤
```bash
mv frontend frontend_backup                          # 如需保留备份，可先备份当前空目录
npx degit vbenjs/vue-vben-admin frontend             # 拉取 Vben Admin 模板
cd frontend
pnpm install  # 或 npm install / yarn install
```

### 对接现有后端接口
- 登录：`POST /api/v1/auth/login`
- 首次管理员创建：`POST /api/v1/auth/admin/init`（单管理员场景，初始化后隐藏注册入口）
- 任务/结果：`/api/v1/tasks`, `/api/v1/results/...` 等

将这些接口封装到 Vben 的 `src/api` 中，并在登录页/业务页中调用。迁移完成后，可删除模板中的示例接口与演示页面，只保留与扫描控制台相关的视图。

### 迁移业务页面
- 登录页：复用 Vben 提供的登录 UI，仅调整接口与单管理员逻辑。
- 扫描控制台：把任务下发、任务列表、结果展示做成一个视图，挂到 Vben 的菜单/路由。

> 说明：当前 `frontend/` 仅保留占位文件，不再包含可运行的前端代码。
