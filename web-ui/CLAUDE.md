[根目录](../CLAUDE.md) > **web-ui**

# web-ui - Vue 3 管理前端

## 模块职责

提供闲鱼监控系统的 Web 管理界面，包括任务管理、结果查看、账号管理、系统设置、实时日志等功能。

## 入口与启动

- `src/main.ts` - 应用入口（创建 Vue 实例，挂载 router + i18n）
- `vite.config.ts` - Vite 构建配置
- `index.html` - SPA HTML 模板

```bash
npm install && npm run dev      # 开发模式（HMR）
npm run build                   # 生产构建（输出到项目根 dist/）
npm run preview                 # 预览构建产物
```

## 对外接口

前端通过 `src/api/` 目录调用后端 REST API：

| API 模块 | 对应后端路由 |
|---------|------------|
| `api/tasks.ts` | `/api/tasks` |
| `api/dashboard.ts` | `/api/dashboard` |
| `api/results.ts` | `/api/results` |
| `api/settings.ts` | `/api/settings` |
| `api/accounts.ts` | `/api/accounts` |
| `api/logs.ts` | `/api/logs` |
| `api/prompts.ts` | `/api/prompts` |

HTTP 客户端封装：`src/lib/http.ts`

## 关键依赖与配置

- `vue` 3.5 + `vue-router` 4 + `vue-i18n` 10
- `reka-ui` (shadcn-vue 底层) + `tailwindcss` 3 + `lucide-vue-next`（图标）
- `@vueuse/core` - 组合式工具
- `class-variance-authority` + `tailwind-merge` - 样式变体管理
- TypeScript 5.9 + Vite 7

## 页面路由

| 路径 | 视图组件 | 功能 |
|------|---------|------|
| `/login` | `LoginView.vue` | 登录 |
| `/dashboard` | `DashboardView.vue` | 概览面板 |
| `/tasks` | `TasksView.vue` | 任务管理 |
| `/accounts` | `AccountsView.vue` | 账号管理 |
| `/results` | `ResultsView.vue` | 监控结果 |
| `/logs` | `LogsView.vue` | 运行日志 |
| `/settings` | `SettingsView.vue` | 系统设置 |

## 测试与质量

- 当前无自动化前端测试
- TypeScript 类型检查：`vue-tsc -b`（构建时执行）

## 相关文件清单

```
web-ui/
├── src/
│   ├── main.ts                 # 应用入口
│   ├── App.vue                 # 根组件
│   ├── router/index.ts         # 路由配置（含鉴权守卫）
│   ├── api/                    # 后端 API 调用层（7 个模块）
│   ├── composables/            # 组合式函数（状态管理）
│   ├── components/
│   │   ├── layout/             # 布局组件
│   │   ├── tasks/              # 任务相关组件
│   │   ├── results/            # 结果相关组件
│   │   ├── settings/           # 设置相关组件
│   │   └── ui/                 # shadcn-vue 基础组件
│   ├── views/                  # 页面视图（7 个）
│   ├── i18n/                   # 国际化（中文/英文）
│   ├── lib/                    # 工具库
│   ├── types/                  # TypeScript 类型定义
│   ├── services/               # WebSocket 服务
│   └── assets/main.css         # Tailwind 入口样式
├── package.json
├── vite.config.ts
├── tailwind.config.cjs
└── tsconfig.json
```
