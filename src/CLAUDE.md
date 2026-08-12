[根目录](../CLAUDE.md) > **src**

# src - 后端核心模块

## 模块职责

Python 后端核心，提供 REST API、爬虫引擎、AI 分析、通知推送、任务调度等全部服务端功能。

## 入口与启动

- `app.py` - FastAPI 应用主入口，注册路由、管理生命周期（启动时初始化 SQLite、重置任务状态、加载定时任务）
- `scraper.py` - Playwright 爬虫核心，拦截闲鱼 API 响应解析商品数据
- `config.py` - 旧版配置兼容层（从 .env 读取常量）

## 对外接口

REST API 路由（前缀 `/api/`）：

| 路由模块 | 前缀 | 功能 |
|---------|------|------|
| `api/routes/tasks.py` | `/api/tasks` | 任务 CRUD、启停、AI 生成 |
| `api/routes/dashboard.py` | `/api/dashboard` | 概览统计 |
| `api/routes/results.py` | `/api/results` | 结果查询、导出、黑名单 |
| `api/routes/settings.py` | `/api/settings` | 通知/AI/爬虫配置管理 |
| `api/routes/accounts.py` | `/api/accounts` | 多账号管理 |
| `api/routes/logs.py` | `/api/logs` | 任务日志查看 |
| `api/routes/prompts.py` | `/api/prompts` | AI Prompt 文件管理 |
| `api/routes/login_state.py` | `/api/login-state` | 登录态管理 |
| `api/routes/websocket.py` | `/ws` | WebSocket 实时推送 |

其他端点：`/health`（健康检查）、`/auth/status`（认证）、`/`（SPA 托管）

## 关键依赖与配置

核心依赖：
- `fastapi` + `uvicorn` - Web 框架
- `playwright` - 浏览器自动化
- `openai` (AsyncOpenAI) - AI 模型调用
- `apscheduler` - 定时任务
- `pydantic-settings` - 配置管理
- `httpx` - HTTP 客户端（通知推送）
- `Pillow` + `pyzbar` - 图片处理/二维码识别

配置入口：`infrastructure/config/settings.py`（Pydantic Settings，单例模式）

## 数据模型

- `domain/models/task.py` - Task / TaskCreate / TaskUpdate / TaskGenerateRequest（Pydantic 模型）
- `domain/repositories/task_repository.py` - TaskRepository 抽象接口
- `infrastructure/persistence/sqlite_task_repository.py` - SQLite 实现
- `infrastructure/persistence/sqlite_bootstrap.py` - Schema 初始化 + 旧数据迁移

## 测试与质量

- 单元测试：`tests/unit/` (22 文件，~100 用例)
- 集成测试：`tests/integration/` (6 文件，~30 用例)
- 冒烟测试：`tests/live/` (需真实凭据)

## 相关文件清单

```
src/
├── app.py                          # FastAPI 主入口
├── scraper.py                      # Playwright 爬虫核心
├── config.py                       # 旧版配置兼容
├── parsers.py                      # 搜索结果/用户数据解析
├── utils.py                        # 工具函数
├── rotation.py                     # 账号/代理轮换池
├── failure_guard.py                # 失败熔断器
├── keyword_rule_engine.py          # 关键词匹配引擎
├── ai_handler.py                   # AI 分析调度（旧版入口）
├── ai_message_builder.py           # AI 消息构建
├── prompt_utils.py                 # Prompt 文件读取/生成
├── api/
│   ├── dependencies.py             # 依赖注入
│   └── routes/                     # 路由模块（9 个）
├── services/                       # 业务服务层（20+ 文件）
├── domain/
│   ├── models/                     # 领域模型
│   └── repositories/               # 仓储接口
├── infrastructure/
│   ├── config/                     # 配置管理
│   ├── persistence/                # SQLite 持久化
│   └── external/                   # 外部客户端（AI、通知）
└── core/
    └── cron_utils.py               # Cron 表达式工具
```
