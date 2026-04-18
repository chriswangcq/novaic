# PR-11  Business `_dispatch_trigger` 迁到 Assembler

| 字段 | 值 |
| --- | --- |
| **Phase** | 1 |
| **Milestone** | M1 |
| **承诺** | R2 |
| **Status** | `[x]` |
| **Depends on** | PR-10 |
| **Blocks** | PR-18 |
| **估时** | 0.5 d |
| **Owner** | __ |
| **PR 标题** | `refactor(business): route _dispatch_trigger through DispatchAssembler` |

## 目标

把 Business 两处手工拼 `/dispatch` 请求（`subagent_send`、`spawn_subagent`）替换为 `DispatchAssembler.assemble_and_dispatch(...)`。保留 `_dispatch_trigger` 函数名作薄壳（PR-18 才删）。

## 范围

- `novaic-business/business/internal/subagent.py`
- 其他直接调 `_dispatch_trigger` 的文件（grep 确认）

## 前置 Checklist

- [x] PR-10 合并
- [x] `rg '_dispatch_trigger' novaic-business/' > /tmp/bus.txt` 清点调用点
- [x] PR-03 的 allowlist 暂时还保留 `subagent.py`（本 PR 合并后应该可以删）

## 实施 Checklist

### 1. 构造全局 Assembler 实例

- [x] `business/main_business.py`（或合适的 DI 位置）：
  ```python
  # 启动期实例化
  resolver = AgentOwnershipResolver(
      business_base_url="http://localhost:8200",  # self-reference 进程内也可直接查 DB
      service_name="business",
  )
  app.state.assembler = DispatchAssembler(
      resolver=resolver,
      queue_base_url=os.environ["QUEUE_SERVICE_URL"],
      service_name="business",
  )
  ```

### 2. 替换 `_dispatch_trigger` 实现

- [x] 保留函数名（PR-18 才删）：
  ```python
  async def _dispatch_trigger(agent_id, trigger_type: str, *, subagent_id=None, metadata=None, message_ids=None):
      """DEPRECATED: kept as thin shim. Removed in PR-18."""
      assembler = ...  # from app.state
      try:
          return await assembler.assemble_and_dispatch(
              TriggerType(trigger_type),
              agent_id,
              subagent_id=subagent_id,
              message_ids=message_ids,
              metadata=metadata,
          )
      except DispatchError as e:
          logger.error("dispatch failed agent=%s trigger=%s kind=%s msg=%s",
                       agent_id, trigger_type, e.kind, e.msg)
          raise
  ```
- [x] **不要吞异常**；原调用方如果本来是 fire-and-forget，本 PR 保持一致（但 log ERROR 而非 WARN）

### 3. 调用点体检

- [x] `subagent_send` 路径：确认传的 `trigger_type` 是 `"subagent_send"`；显式 `message_ids=[<just-written-msg-id>]`
- [x] `spawn_subagent` 路径：同上，`trigger_type="spawn_subagent"`；`metadata={"initial_context": ...}` 保留
- [x] 若原先传 `"user_response"` → 改 `"user_message"`（PR-09 已准备好）

## 测试 Checklist

- [x] 单测 mock Assembler → 验证 subagent_send / spawn_subagent 各自传参正确
- [x] 集成（本地）：
  - 发一条 SUBAGENT_SEND → Queue Service 收到 200 OK
  - SPAWN_SUBAGENT → 同上
- [x] 回归：观察 Business 日志无新增报错

## 可观测性 Checklist

- [x] Business 侧 log：`event=dispatch via=assembler trigger=... agent=... result=ok|...`
- [x] Queue Service `dispatch_total{caller=business}` 正常上升

## 文档 Checklist

- [x] [message-wake-refactor.md](../message-wake-refactor.md) P1-6 → `[x]`
- [x] 本工单 Status → `[x]`
- [x] 如果 PR-03 allowlist 里有 `subagent.py`，**从 allowlist 删掉**（本 PR 合并后直调已消失）

## 验收命令

```bash
rg 'httpx\..*/dispatch' novaic-business/
# 预期空
rg '_dispatch_trigger' novaic-business/
# 仅剩 def + 调用点（薄壳尚存）
```

## 回滚

`git revert` — 若 Assembler 有 bug，revert 后回到手工拼字段状态。

## 备注

- 不要在本 PR 里删 `_dispatch_trigger`（那是 PR-18），因为此时 HealthWorker/Scheduler 可能还没迁完。
- 观察 hihi 重现场景：SPAWN_SUBAGENT 路径应当不再受影响。
