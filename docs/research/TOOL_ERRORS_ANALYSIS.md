# subagent_cancel 问题分析

## 1. subagent_cancel - 执行失败

### 调用链

```
Tools Server call_tool
  → executor.execute("subagent_cancel")
  → client.post("/internal/agents/{agent_id}/subagent/{target_subagent_id}/cancel")
  → Gateway agent_subagent_cancel
  → 1. subagent_repo.get_by_id() 查 subagent
  → 2. 若 status != "running" → return { success: False, reason: "SubAgent is not running (status: xxx)" }
  → 3. subagent_repo.set_cancelled()
  → 4. RO client.forward("POST", "/internal/runtimes/cancel-by-subagent", ...)
  → 5. return { success: True }
```

### 根因分析

**Gateway agent_subagent_cancel**（`gateway/api/internal/agent.py` 638-660 行）:
```python
if subagent.status != SubagentStatus.RUNNING.value:
    return {"success": False, "reason": f"SubAgent is not running (status: {subagent.status})"}
```

**典型失败场景**：
1. **子任务已结束**：subagent 已是 `completed` / `failed` / `cancelled` / `sleeping`，再调 cancel 会返回 `success: False`
2. **子任务不存在**：`get_by_id` 返回 None → 404
3. **RO 转发失败**：`client.forward` 异常（网络、RO 未启动等）

**语义**：`subagent_cancel` 只对 **running** 状态的子任务有效。对已结束的子任务调用属于误用，会得到「执行失败」。

### 结论

**设计符合预期**：cancel 仅对 running 子任务有效，对已结束子任务返回失败是预期行为。

**可能改进**（暂不实现）：
- 对「SubAgent is not running」做语义区分：可返回 `success: True` + `message: "SubAgent already finished (status: completed)"`，表示「无需取消，已结束」
- 或在工具描述中明确：仅在子任务 running 时调用，否则会失败

---

## 附：mobile_file_list 已删除

`mobile_file_list` 因返回格式与 TRS 不兼容（`files` 无 `url`）导致 422、Saga 失败，已于 2025-03 删除。详见 `docs/MOBILE_FILE_LIST_REMOVAL_PLAN.md`。
