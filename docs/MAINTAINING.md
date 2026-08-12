# 维护与发布流程

本文档面向本仓库（社区续维分支）的维护者与贡献者。

## 仓库拓扑

```
origin    https://github.com/LemonYangZW/ai-goofish-monitor   (读写，日常开发)
upstream  https://github.com/Usagi-org/ai-goofish-monitor     (只读，已归档)
```

`upstream` 的 push 地址已设为 `DISABLED`，避免误推到归档仓库：

```bash
git remote set-url --push upstream DISABLED
```

上游已归档、不再接受 PR，因此同步是**单向**的。归档前遗留的 `claude/issue-*` 分支仍可作为素材 cherry-pick。

## 分支模型

| 分支 | 用途 |
|------|------|
| `master` | 主干，始终保持可发布状态 |
| `feat/*` `fix/*` | 功能与缺陷分支，经 PR 合入 `master` |

合入 `master` 前必须通过 `Tests` workflow。

## 从上游获取遗留改动

```bash
git fetch upstream
git log --oneline master..upstream/master     # 查看差异
git merge upstream/master                      # 或 cherry-pick 单个提交
```

## 版本规则

采用语义化版本，统一带 `v` 前缀（上游历史中 `2.2`/`2.3`/`2.4` 缺前缀，本仓库起统一）。

- **major** — 不兼容的配置或数据结构变更（需提供迁移说明）
- **minor** — 新增功能，例如 `v2.5.0` 包含 CF WAF 绕过与 AI 流式调用
- **patch** — 缺陷修复与依赖更新

版本号的单一事实来源是 `pyproject.toml` 的 `[project] version`，发布时须与 git tag 一致。

## 发布步骤

1. 确认 `master` 上 `Tests` workflow 通过
2. 更新 `pyproject.toml` 中的 `version`
3. 整理变更记录，提交
4. 打 tag 并推送：

   ```bash
   git tag -a v2.5.0 -m "Release v2.5.0"
   git push origin v2.5.0
   ```

5. 在 GitHub 创建 Release，说明变更内容与升级注意事项

## 持续集成

| Workflow | 触发 | 说明 |
|----------|------|------|
| `tests.yml` | push to `master` / PR / 手动 | Python 3.11 与 3.13 双版本跑 pytest，附覆盖率 |
| `docker-image.yml` | PR 合并到 `master` / 手动 | 构建并推送镜像至 `ghcr.io/<owner>/ai-goofish` |
| `claude.yml` | issue / PR 中 `@claude` | **需要配置 `OPENAI_API_KEY` secret**，未配置时该 workflow 会失败；不使用可直接删除 |

`docker-image.yml` 使用 `github.repository_owner` 与内置 `GITHUB_TOKEN`，fork 后无需额外配置即可工作。

## 本地校验

```bash
pytest -m "not live and not live_slow"        # CI 等价命令
coverage run -m pytest -m "not live and not live_slow" && coverage report
```

`live` / `live_slow` 用例需要真实闲鱼登录态与 AI 凭据，仅在本地手动执行。

## 依赖说明

`requirements.txt` 未锁定版本，上游依赖变更可能引入回归。排查异常行为时，建议先用 `pip freeze` 比对实际安装版本。
