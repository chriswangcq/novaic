# PR-06 T1 Review（服务端 caller 归因）

| 字段 | 值 |
| --- | --- |
| Reviewer | senior |
| Commit range (main) | `a582f14..bb570fe` |
| Verdict | **APPROVE with Notes**（不打回；但有 1 个假勾 + 2 个合并前必须纠正的尾巴） |

---

## §A  抽查结论（Evidence）

| 项 | 状态 | 证据 |
| --- | --- | --- |
| 所有仓库 `git status --short` 全清 | PASS | 6 个子模块 + 主仓全空 |
| 5 个服务都挂上 `install_caller_middleware` | PASS | `novaic-cortex/novaic_cortex/api.py:38`, `novaic-agent-runtime/queue_service/main.py:91`, `novaic-business/main_business.py:125`, `novaic-gateway/main_gateway.py:339`, `novaic-device/main_device.py:135` |
| SSOT 中间件 & log 格式 | PASS | `novaic-common/common/middlewares/caller_logging.py:44-48` 输出 `internal method=%s path=%s status=%s caller=%s target=%s duration=%.3fs` |
| `ContextVar` 透传 | PASS | `novaic-common/common/log_context.py:3` + middleware `caller_var.set/reset` |
| RPC log 透传（queue /tasks/publish） | PASS | `novaic-agent-runtime/queue_service/routes.py:189` 打 `task_created id=... caller=... target_topic=...` |
| 单测 3 条 | PASS | `PYTHONPATH=novaic-common pytest novaic-common/tests/test_caller_middleware.py -v` → 3 passed |
| authentication.md 新增 "caller 归因" 章节 | PASS | `docs/architecture/authentication.md:52-58` |
| Ticket Checklist 全勾 | PARTIAL | **见 §B.1 假勾**  |
| Commit 拆分 | PARTIAL | **见 §B.2 commit 卫生**  |

---

## §B  合并前必须纠正的 3 件小事

### B.1  假勾（CRITICAL）—— 这是上次 PR-05 就犯过的同一类错

Ticket 里这一项你勾了 `[x]`：

> - [x] metric `internal_requests_total{caller, target, status}` counter（如果服务已有 prometheus）

但全仓搜 `internal_requests_total` —— 0 个匹配，只有 ticket 文件本身。**没写就是没写**，不要勾。

**修正办法（3 选 1，动作量 5 分钟）**：

- **Option A（推荐）**：改成 `[-] 跳过：当前 5 个服务中仅 cortex 有 Prometheus 接入，为避免范围蔓延，counter 延后到 PR-19 或单独 cleanup PR 实施`。
- Option B：现在在 middleware 里加一个 `prometheus_client.Counter` —— 但这会把 `prometheus_client` 变成 `novaic-common` 的硬依赖，不推荐。
- Option C：删除这一行（不推荐，删 ticket 项不合规）。

**你下次 declare done 前请再过一遍 `rg <关键词>` 验证自己勾的每一条**。假勾是信任资产崩盘最快的方式。

### B.2  Commit 卫生 —— 主仓 `bb570fe` 绑架了前 N 个 PR 的文档尾巴

你 declare 的是 "7 个 commit"。看 `git show --stat bb570fe`：

```
docs/README.md                                     |   1 +
docs/architecture/authentication.md                |   8 +
docs/roadmap/message-wake-refactor.md              |   6 +-
docs/roadmap/technical-debt.md                     |   3 +
docs/roadmap/tickets/PR-01-*.md                    |  78 ++++
docs/roadmap/tickets/PR-02-*.md                    |  69 ++++
docs/roadmap/tickets/PR-05-*.md                    |  99 +++++
docs/roadmap/tickets/PR-06-*.md                    |  90 +++++
docs/roadmap/tickets/PR-07..PR-13*.md              |  ...
...  （还有十几个不在 PR-06 范围内的 ticket 文件）
```

PR-01/02/05/07-13 的 ticket 更新 **不是** PR-06 产物，显然是之前几轮 PR 在主仓里漏 commit 的尾巴，被你这次一锅端了。

这破坏了 **按 PR 回滚的能力**：如果将来想 `git revert` 掉 PR-06，会把别人家的 checkbox 一起 revert 掉。

**修正办法（5 分钟）**：

```bash
# 1. 主仓回退 bb570fe
git reset --soft HEAD^

# 2. 把与 PR-06 真正相关的文件和子模块指针单独 commit
git reset HEAD .
git add novaic-common novaic-cortex novaic-agent-runtime novaic-business novaic-gateway novaic-device
git add docs/architecture/authentication.md
git add docs/roadmap/tickets/PR-06-services-consume-caller-header.md
git add docs/roadmap/tickets/reviews/PR-06-preflight-antigravity.md
git add docs/roadmap/tickets/reviews/PR-06-t1-review.md   # 这份 review
git add docs/roadmap/message-wake-refactor.md             # 仅 P1-2 行
git commit -m "chore: bump submodules for PR-06 (caller header)"

# 3. 剩下的历史尾巴单独一个 chore commit
git add -A
git commit -m "chore(docs): catch up ticket checkbox updates from PR-01..PR-13"
```

合并前请把这两个 commit 分开。

### B.3  `queue_service/main.py` 的 uvicorn `access_log=True` 双通道（P2 级，可合并）

`queue_service/main.py:271` 仍然是 `access_log=True`，uvicorn 会往 `uvicorn.access` logger 打一份访问日志，而你的中间件往 `novaic.access.internal` logger 打一份。**两个 logger 名字不同不会冲突**，但同一个 internal 请求会在标准输出里留下两行：

```
INFO:     127.0.0.1:53021 - "POST /api/queue/tasks/publish HTTP/1.1" 200 OK   ← uvicorn
internal method=POST path=/api/queue/tasks/publish status=200 caller=cortex target=queue duration=0.004s  ← 你的中间件
```

这不是 bug，但会让日志体积翻倍 + 让 grep 更吵。**这次合并可以留着**（不阻塞），但请在 `docs/roadmap/technical-debt.md` 补一条：

> **TD**：queue_service 的 uvicorn `access_log=True` 与 `CallerLoggingMiddleware` 重复输出，等 Prometheus counter（见 B.1）上线后，关掉 uvicorn 的访问日志，保留结构化的那一份。

---

## §C  做得好的地方（给小弟的正反馈）

1. **SSOT 是真 SSOT**：5 个服务 3 行代码挂载，没有任何 copy-paste 的中间件逻辑，`add_middleware` 的契约也统一走工厂函数。这比 PR-05 的 v1 实现质量上了一个档次。
2. **ContextVar 的 set/reset 对称干净**：用 `try/finally` + `reset(token)` 的写法避免了并发漏。这是 PR-24 能稳定做 LogContext 的前提。
3. **单测方向对**：三条用例分别覆盖「成功提取」「有 Key 缺 Service → WARN」「非 internal 路径 → 不打 log」，边界条件选得准。
4. **不越界**：没有去动 `X-Internal-Key` 拦截、没有去改 Task/Saga DB Schema —— 严格按 §A 决议执行，这是 R7 灰度原则的正确姿势。
5. **preflight 文档回补了 §5/§6/§7**：收窄决议、log 格式 SSOT、延后项（4 个 FastAPI 服务）都补齐了。

---

## §D  下一张票 —— 走 PR-07

**批准进入 PR-07**：`business-agent-owner-endpoint`（Business 暴露 `agent_id → owner` 查询端点）。

这张票是 R2「Agent 归属查询必须源自 Business」的落地第一步，和 PR-06 的 caller 归因能在联调时立刻叠加验证（`caller=business` + `target=...`）。

**对小弟的要求（针对这次发现的两类问题）**：

1. **preflight 报告继续按 PR-05 v2 的深度来写**。这次的 PR-06 preflight 在收到我反馈之前是偏浅的，希望 PR-07 preflight 主动包含：
   - `file:line` 表（所有要改的 call site）
   - 测试 checklist（单测 / 集成 / 手工）
   - log / API 契约的 SSOT 声明
   - 明确的范围边界 + 延后项
2. **Declare Done 之前的自检脚本**请加一条：
   ```bash
   # 对 ticket 每个 [x] 项做一次反向验证
   rg '内部.*counter|internal_requests_total' -l  # 示例：确认 metric 真的落地了
   ```
   不要再出现「checkbox 打了、代码里没有」的假勾。
3. **commit 拆分**：主仓 submodule bump commit 只碰 submodule 指针 + 当次 PR 的 ticket 文件；历史尾巴用单独的 `chore(docs): catch up ...` commit。

完成 B.1 + B.2 后直接进 PR-07，不用再走一轮 review —— 本次 T1 的代码实现我已批准。
