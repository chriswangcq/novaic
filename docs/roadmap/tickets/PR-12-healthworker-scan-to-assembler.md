# PR-12  HealthWorker `_scan_unhandled_messages` 迁到 Assembler

| 字段 | 值 |
| --- | --- |
| **Phase** | 1 |
| **Milestone** | M1 |
| **承诺** | R2 + R3 + R7 |
| **Status** | `[x]` |
| **Depends on** | - [x] PR-10 合并
- [x] PR-11 / PR-13 顺序无强依赖，可与它们并行 |
| **Blocks** | PR-19 |
| **估时** | 0.5 d |
| **Owner** | __ |
| **PR 标题** | `refactor(runtime): HealthWorker._scan_unhandled_messages uses DispatchAssembler` |

## 目标

修掉 hihi 事件里两条核心 bug：
1. 硬编码 `user_id=""` → `400 Bad Request`（R3 修复：Assembler 自动解 user_id）
2. 裸 `httpx.Client()` 调 `/recover/all` → `401 Unauthorized`（R7 修复：用 `internal_client(service_name="runtime-health")`）

> 注意：本 PR **不**删 `_scan_unhandled_messages` 的职责（那是 PR-19）。此步只是让它先不 400 / 不 401。

## 范围

- `novaic-agent-runtime/task_queue/workers/health_worker_sync.py`

## 前置 Checklist

- [ ] PR-10 合并；`DispatchAssembler` 可用
- [ ] PR-05 合并；`internal_client(service_name=...)` 可用
- [ ] `rg "httpx\.Client\(\)" novaic-agent-runtime/task_queue/workers/' ` 清点裸 client 点

## 实施 Checklist

### 1. 构造 worker 级 Assembler / recovery client

- [ ] Worker 启动期：
  ```python
  self._assembler = DispatchAssembler(
      resolver=AgentOwnershipResolver(
          business_base_url=os.environ["BUSINESS_INTERNAL_URL"],
          service_name="runtime-health",
      ),
      queue_base_url=os.environ["QUEUE_SERVICE_URL"],
      service_name="runtime-health",
  )
  self._recover_client = internal_client(
      service_name="runtime-health",
      base_url=os.environ["QUEUE_SERVICE_URL"],
  )
  ```
- [ ] 两条客户端都有 fail-fast（env 缺失直接崩）

### 2. 替换 `_scan_unhandled_messages` 里的 dispatch

- [x] 注入 `get_assembler()` factory
- [x] 将 `_scan_unhandled_messages` 内部手工 `POST /api/queue/dispatch` 换为 `assemble_and_dispatch(TriggerType.USER_MESSAGE, ...)`
- [x] **语义明确化**：既然都是通过读 `messages` 表扫出来的 orphan message，直接使用 `TriggerType.USER_MESSAGE`
- [x] 幂等保护：传入 `idempotency_key = f"health_fallback:{msgs[-1]['id']}"`，利用队列侧的历史 session 查询避免重复触发，并且限制 `MAX_FALLBACK_PER_TICK = 50`。
- [x] 取消空 `user_id=""` 的硬编码，改由 Assembler 的 OwnershipResolver 自动补全。
- [x] 修改 `health_worker_sync` 为 async def 循环，并在最后释放 `aclose`。 # 这组未处理消息
      )
  except DispatchError as e:
      if e.kind == "no_owner":
          logger.error("orphan detected: agent_id=%s has no owner; leaving pending", agent_id)
          # 不再 re-dispatch，让 PR-26 的 emitter 来报警
      else:
          logger.warning("fallback dispatch failed kind=%s agent=%s", e.kind, agent_id)
- [ ] 移除任何 `user_id=""` 的硬编码
- [ ] 注意：`/internal/messages/unread-grouped` 返回的 key 可能按 `agent_id` 聚合；直接用 agent_id 即可（Assembler 自己解 user_id）

### 3. 替换 `_perform_check` 的 `/recover/all` 调用

- [ ] 把裸 `httpx.Client().post(...)` 改为 `await self._recover_client.post("/api/queue/recover/all")`
- [ ] 401 / 5xx 的处理路径保留（log + 下个 tick 重试）

### 4. 处理 env 缺失

- [ ] `BUSINESS_INTERNAL_URL` / `QUEUE_SERVICE_URL` 启动期不可为空
- [ ] Worker 无法构造 Assembler → 进程退出（fail-fast）或 log CRITICAL 循环 sleep（保持与现状一致）

## 测试 Checklist

- [x] 单测：由于这个 worker 是被动扫描，主要验证 mock 调用的 `trigger_source` 和 `agent_id` 正确，以及 `user_id` 未被强传。
- [x] 如果抛 `DispatchError(no_owner)`，降级为 `warning` 或 `error` 即可，跳过本条。**不**尝试 `user_id=""`
- [ ] 本地集成：
  - 发一条 USER_MESSAGE 但不触发前端路径（模拟 hihi 场景）
  - HealthWorker 30s 后扫描 → 日志应当是 `dispatch result=ok`，**不再**是 `API error (400): user_id is required`

## 可观测性 Checklist

- [x] log：`event=health_fallback agent=... messages=... result=...`
- [x] 针对 `MAX_FALLBACK_PER_TICK` 提供 `fallback_dispatched` metrics 和超限警告 `event=health_fallback_capped`。ok|no_owner|queue_4xx|queue_5xx|network}` counter
- [ ] `/recover/all` 日志包含 `caller=runtime-health` + `status=200`（PR-06 支持下）

## 文档 Checklist

- [x] [message-wake-refactor.md](../message-wake-refactor.md) P1-9 → `[x]`
- [x] 本工单 Status → `[x]`
- [x] 清理 `task_queue/client.py` 中的 `dispatch`
- [x] 从 `scripts/ci/lint_dispatch.sh` 的 `ALLOWLIST` 删除 `task_queue/client.py`
- [ ] 更新 PR-03 allowlist：移除 `health_worker_sync.py`

## 验收命令

```bash
# 重现 hihi 场景
./scripts/reset-agent-data.sh
# 发一条消息（绕过正常路径）直接写 entangled
# 等 30s 看 log
tail -f health.log | rg 'dispatch'
# 预期：result=ok；无 400/401
```

```bash
rg 'user_id=""' novaic-agent-runtime/
# 预期：空（或仅测试文件）
rg 'httpx\.Client\(\)' novaic-agent-runtime/task_queue/
# 预期：空
```

## 回滚

`git revert` — 回滚即回到 hihi 时代的 400/401 模式。不建议保留 revert 超过 1 天。

## 备注

- 这是**立即修 hihi**的 PR（虽然不是终极解）；合完可以先测一轮"发消息能不能回复"。
- 终极解在 PR-15/16/17/18：主路径从 HealthWorker 转移到 subscriber。
