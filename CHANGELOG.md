# 更新日志

本文件记录本仓库（社区续维分支）的重要变更。

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [2.5.0] - 未发布

接手上游归档项目后的首个版本。重点是恢复爬虫可用性、修复长期潜伏的缺陷，并建立质量基线。

### 修复

- **爬虫因请求头注入而完全失效**（`src/scraper.py`）
  浏览器快照中的 `Sec-Fetch-*`、`Accept-Encoding`、`Accept`、`Referer` 等请求头被无差别注入到每一个请求。前三者属于浏览器保留头，由 Chromium 按请求类型自行计算，强行覆盖会触发 `net::ERR_INVALID_ARGUMENT`；后两者取自采集时的某个 XHR，套用到文档导航与脚本加载上语义不符。
  后果是页面 JS 资源加载不全、风控组件 `baxia` 初始化失败、搜索页不发出任何 mtop 请求，最终被上层误判为"登录态失效"。
  现改为仅保留 `Sec-CH-UA` 系列与 `Accept-Language` 等指纹相关头。修复后搜索页请求数由 31 恢复至 289，mtop 接口由 0 恢复至 68。

- **任务失败熔断从未生效**（`src/failure_guard.py`）
  `_update_task` 在持有状态文件句柄的同时执行原子替换，Windows 上 `os.replace`/`os.remove` 因文件被占用而失败，兜底分支静默丢弃整次写入，导致 `consecutive_failures` 永远无法累积、熔断与限流形同虚设。
  同时 `a+` 模式创建的空文件会被 `_read_json_file` 误判为"损坏"并转存为 `.corrupt.<ts>`，长期堆积无用残留。
  现将文件锁移至独立 `.lock` 文件，并将空文件正确识别为初始状态。

- **pytest 无法收集任何用例**（`src/ai_handler.py`）
  模块导入时调用 `sys.stdout.detach()` 夺走底层 buffer，使 pytest 持有的流对象失效，报 `underlying buffer has been detached`。改用 `reconfigure(encoding="utf-8")` 原地重设编码，对已被接管的流自动跳过。

- **Docker 构建产物路径冲突**（`.dockerignore`）
  移除 `web-ui/dist` —— 该条目与"前端产物统一输出到根目录 `dist/`"的约定冲突，且此前已由测试覆盖检出。

### 新增

- **CI 测试流水线**（`.github/workflows/tests.yml`）
  Python 3.11 / 3.13 双版本矩阵执行 pytest 并输出覆盖率。此前仅有 Docker 构建流水线，是失效测试长期无人察觉的直接原因。
- **维护文档**（`docs/MAINTAINING.md`）
  记录仓库拓扑、上游同步方式、分支模型、版本规则与发布步骤。
- **项目元数据**（`pyproject.toml`）
  补充 `[project]` 段，作为版本号的单一事实来源。

### 改进

- **登录态失效报错不再武断**（`src/scraper.py`）
  原文案将"搜索页零 mtop 响应"一律归因于"Cookie 已过期"，会把排查引向错误方向。现增加 `requestfailed` 监听统计资源加载失败数，并据此给出方向性提示；其余可能原因一并列出，异常类型保持不变以免影响熔断与自动恢复逻辑。

### 测试

- 修复 21 个失效用例，全量测试由 `21 failed / 101 passed` 恢复为 `127 passed`，覆盖率 61%。
  - AI 调用改为流式后，mock 仍返回非流式响应对象（11 个）
  - 响应解析归一化行为缺少覆盖（3 个）
  - `/api/settings/ai/test` 端点已重写为 httpx，测试仍在 mock `openai` SDK（1 个）
  - 存储层新增 `_status` 字段后断言未更新（1 个）
  - Windows 环境变量名不区分大小写导致的平台性失败（1 个，改为跳过）
  - 其余为分支落后与配置漂移
- **修复测试污染**：`load_dotenv(override=True)` 会把测试用 `.env` 写入 `os.environ` 并泄漏到后续用例，在 `conftest.py` 增加 autouse fixture 快照/恢复环境变量；任务生成端点会写入真实 `prompts/` 目录，改为切换工作目录隔离。
- 新增用例覆盖请求头过滤、AI 响应归一化与 AI 测试端点的三条路径。

### 待处理

- 本分支落后上游 `master` 9 个提交，其中包含路径遍历安全修复（`6c2dc95`）。当前 `/api/prompts/{filename}` 端点仍使用 `"/"` 与 `".."` 黑名单校验，**在 Windows 上无法拦截 `C:\...` 形式的绝对路径**，需尽快同步。

---

## 上游历史版本

以下版本由上游 [Usagi-org/ai-goofish-monitor](https://github.com/Usagi-org/ai-goofish-monitor) 维护，该仓库已于 2026 年 5 月归档。完整记录请参见上游提交历史。

| 版本 | 日期 |
|------|------|
| 2.4 | 2026-04-27 |
| 2.3 | 2026-03-18 |
| 2.2 | 2026-03-16 |
| v2.1 | 2026-03-13 |
| v2.0 | 2026-03-11 |
| v1.3 | 2026-03-09 |
| v.1.2 | 2026-03-04 |
| v1.1 | 2026-03-03 |
| v1.0.0 | 2026-01-12 |
