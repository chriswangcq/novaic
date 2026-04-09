Batch 12/22 — 8 files
REPO_ROOT=/Users/wangchaoqun/new-build-novaic

Files in this batch (one subagent per file):
  - docs/runbooks/ARCHITECTURE-SERVICES-AND-HANDLERS.md
  - docs/misc/CLIENT_DB_ARCHITECTURE.md
  - docs/misc/CROSS_PLATFORM_ARCHITECTURE.md
  - docs/misc/CURRENT_STATE_SURVEY_SUMMARY.md
  - docs/runbooks/E2E_READINESS.md
  - docs/misc/FRONTEND_HOT_UPDATE_SUMMARY.md
  - docs/runbooks/HOT_UPDATE_DEPLOY_STEPS.md
  - docs/misc/IOS_BLACK_SCREEN_ISSUE_REPORT.md

---
Use SKEPTICAL_VERIFY_TEMPLATE.md substituting PATH_FROM_REPO_ROOT for each line above.
# 单文件持疑核验（Subagent / 人工通用）

**仓库根**：`<REPO_ROOT>`（本机填绝对路径）  
**唯一目标文件**（本轮只读这一份）：`<PATH_FROM_REPO_ROOT>` 例：`docs/foo.md` 或 `HANDOVER.md`

---

## 指令（复制给 subagent）

你是**持疑**的文档审计员。只打开并分析下面这一个文件：

`/<REPO_ROOT>/<PATH_FROM_REPO_ROOT>`

1. **提取**文中所有可证伪陈述：端口、路径、文件名、类/函数名、HTTP 路由、DB 表名、进程名、环境变量、部署命令、`git` 路径。
2. **在代码库中搜索**（`novaic-gateway`、`novaic-agent-runtime`、`novaic-cortex`、`Entangled`、`entangled-service`、`novaic-common`、`deploy`、`scripts` 等），逐条标记：
   - **VERIFIED** — 给出仓库内文件路径 + 符号或行号范围  
   - ...
