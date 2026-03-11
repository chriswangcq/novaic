# 研究报告：Gateway VM Fallback vs RO VM 实现差异

## 一、代码对比结论

**Gateway 与 RO 的 vm.py 实现完全相同**，逐行一致。

- `novaic-gateway/gateway/api/internal/vm.py`
- `novaic-runtime-orchestrator/gateway/api/internal/vm.py`

两者都包含：
1. `maybe_forward_to_runtime_orchestrator` 调用
2. 相同的 fallback 逻辑：`RuntimeRepository.get_by_id` → `get_agent_config_manager` → `VM_TOOLS`

---

## 二、关键差异：数据源不同

### 2.1 数据库分离

| 服务 | DB 文件 | agent_runtimes 表 |
|------|---------|-------------------|
| **Gateway** | `gateway.db` | 存在但 **v40 迁移已清空**（Gateway 不持有 runtimes） |
| **RO** | `runtime_orchestrator.db` | 有实际数据，RO 拥有 runtimes |

来源：
- Gateway schema v40: `DELETE FROM agent_runtimes`（"Gateway does not own runtimes"）
- CONTEXT_SUMMARY: "B2 Split：Gateway 管 Agent/SubAgent，Runtime Orchestrator 管 Runtime；Gateway 不持有 agent_runtimes"

### 2.2 Fallback 行为差异

| 步骤 | Gateway Fallback | RO Fallback |
|------|------------------|-------------|
| 1. `RuntimeRepository.get_by_id(runtime_id)` | 查 `gateway.db` 的 agent_runtimes → **空表，返回 None** | 查 `runtime_orchestrator.db` → **有数据** |
| 2. `if not runtime` | **抛出 404** | 正常继续 |
| 3. `get_agent_config_manager().get_agent(agent_id)` | 查 `gateway.db` 的 agents | 查 `runtime_orchestrator.db` 的 agents |
| 4. 返回 VM_TOOLS | 不会执行到 | 正常返回 |

**结论：Gateway 的 vm-tools fallback 在 B2 架构下不可用**，因为 `agent_runtimes` 已被清空，`get_by_id` 恒为 None，会直接 404。

---

## 三、Agent 配置差异

| 服务 | agents 表所在 DB | 说明 |
|------|------------------|------|
| Gateway | gateway.db | 通常为 Agent 配置主数据源 |
| RO | runtime_orchestrator.db | 独立 DB，agents 可能不同步 |

两边的 `get_agent_config_manager` 都读各自 DB 的 agents 表。若部署为独立进程且 DB 分离，agent 的 vm 配置可能不一致。

---

## 四、vm-tools 调用方

全仓库搜索 `vm-tools` 或 `get_runtime_vm_tools`：

- **当前生产代码**：未发现对 `/internal/runtimes/{id}/vm-tools` 的调用
- **Tools Server**：VM 工具来自 `get_all_tools()` 中的 `VM_TOOLS`（builtin），不依赖 vm-tools API
- **测试脚本**：`novaic/scripts/archive/root-legacy-scripts/test_vm_tools_discovery.py` 中有调用，属于归档脚本

---

## 五、流程对比

### 5.1 Gateway 收到 vm-tools 请求（当前会转发）

```
请求 GET /internal/runtimes/rt-xxx/vm-tools
  → maybe_forward 匹配 /internal/runtimes
  → 转发到 RO
  → RO 处理（RO 的 maybe_forward 返回 None，走本地）
  → RO: RuntimeRepository.get_by_id ✓（有数据）
  → RO: get_agent_config_manager ✓
  → 返回 {tools, agent_id, vm_available}
```

### 5.2 Gateway 收到 vm-tools 请求（若不转发）

```
请求 GET /internal/runtimes/rt-xxx/vm-tools
  → maybe_forward 返回 None（_RO_FORWARDED_PREFIXES 为空）
  → Gateway fallback
  → Gateway: RuntimeRepository.get_by_id ✗（agent_runtimes 为空）
  → 404 "Runtime not found"
```

---

## 六、结论与建议

### 6.1 结论

1. **代码一致**：Gateway 与 RO 的 vm.py 完全相同。
2. **数据源不同**：Gateway 的 agent_runtimes 已清空，fallback 会 404。
3. **调用方**：当前生产代码未发现 vm-tools 调用，可能为遗留 API。

### 6.2 若实施「Gateway 全部不转发」

- **方案 A（清空 _RO_FORWARDED_PREFIXES）**：vm-tools 会走 Gateway fallback → **必然 404**。
- **方案 C（调用方直连 RO）**：若未来有调用方，应改为直连 RO 的 vm-tools。
- **方案 B（移除 maybe_forward）**：与方案 A 效果相同，vm-tools 在 Gateway 上会 404。

### 6.3 建议

1. **确认 vm-tools 是否仍在使用**：若无调用方，可考虑废弃该 API。
2. **若需保留 vm-tools 且不转发**：需在 Gateway 侧增加从 RO 获取 runtime 的能力（例如通过 `client.forward` 查 RO 的 runtime），再在 Gateway 中做 agent 配置校验并返回 VM_TOOLS，而不是依赖本地 agent_runtimes。
3. **若采用方案 C**：让调用方直连 RO 的 `/internal/runtimes/{id}/vm-tools`，Gateway 可删除该端点。
