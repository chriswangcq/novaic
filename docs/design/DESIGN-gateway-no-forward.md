# 设计方案：Gateway 全部不转发到 RO

## 一、现状

### 1.1 当前转发机制

- `maybe_forward_to_runtime_orchestrator()`：入站请求若匹配 `_RO_FORWARDED_PREFIXES`，则转发到 RO
- `_RO_FORWARDED_PREFIXES`：`["/internal/runtimes", "/internal/rt/"]`
- 实际会转发的路径：`/internal/runtimes/*`、`/internal/rt/*`

### 1.2 实际转发情况

| 文件 | 使用 maybe_forward 的路径 | 是否真正转发 |
|------|--------------------------|--------------|
| **vm.py** | `/internal/runtimes/{id}/vm-tools` | ✅ 会转发 |
| **subagent.py** | `/internal/subagents/*` | ❌ 不转发（不在前缀中） |
| **message.py** | `/internal/messages/*` | ❌ 不转发 |
| **agent.py** | 无 maybe_forward | - |

此外，**agent.py** 和 **subagent.py** 在处理逻辑中会**主动调用** `client.forward()` 到 RO（如 cancel-by-subagent、runtimes/latest），这是 Gateway 作为客户端调用 RO，不是入站请求的转发。

### 1.3 唯一实际转发的端点

- `GET /internal/runtimes/{runtime_id}/vm-tools`（vm.py）
- 调用方：Tools Server 发现 VM 工具
- 转发后：RO 的 vm.py 处理，使用 RO 的 RuntimeRepository + agent config

---

## 二、目标

**Gateway 入站请求全部本地处理，不再转发到 RO。**

- 入站：Gateway 收到的 `/internal/*` 请求，全部本地处理
- 出站：Gateway 处理请求时仍可主动调用 RO（`client.forward`），用于 cancel/delete runtime 等

---

## 三、设计方案

### 方案 A：清空转发前缀（最小改动）

**改动**：`helpers.py` 中 `_RO_FORWARDED_PREFIXES = []`

**效果**：
- `maybe_forward_to_runtime_orchestrator` 对所有路径返回 `None`
- 所有端点走本地 fallback
- subagent.py、message.py、vm.py 的 maybe_forward 调用变为「恒不转发」，逻辑不变

**前置条件**：
- vm.py 的 `/internal/runtimes/{id}/vm-tools` 必须有可用的本地 fallback
- 当前 vm.py 已有 fallback：`RuntimeRepository.get_by_id` + `get_agent_config_manager`

**数据一致性**：
- Gateway 与 RO 若共享 DB，Gateway 的 RuntimeRepository 可读到 runtime 数据 → fallback 可用
- 若 Gateway 与 RO 使用不同 DB，runtime 数据在 RO → fallback 可能 404，需确认部署架构

---

### 方案 B：移除 maybe_forward，统一本地处理（推荐）

**改动**：

1. **helpers.py**
   - 删除 `_RO_FORWARDED_PREFIXES`
   - 将 `maybe_forward_to_runtime_orchestrator` 改为恒返回 `None`（或直接删除，调用处改为不调用）

2. **调用方**
   - subagent.py、message.py、vm.py：删除 `proxied = await maybe_forward_to_runtime_orchestrator(...)` 及 `if proxied is not None: return proxied` 分支
   - 仅保留本地处理逻辑

**效果**：
- 代码更清晰，无死代码
- 所有 internal API 明确为「Gateway 本地处理」

**工作量**：需修改 subagent.py（约 20 处）、message.py（约 15 处）、vm.py（1 处）

---

### 方案 C：调用方直连 RO（架构级调整）

**思路**：Gateway 不再暴露会转发的 internal 路径，由调用方直接请求 RO。

**改动**：
1. Gateway 删除 `/internal/runtimes/{id}/vm-tools` 端点
2. Tools Server 配置 `RUNTIME_ORCHESTRATOR_URL`，调用 `GET {RO_URL}/internal/runtimes/{id}/vm-tools`
3. 其他 internal 路径若需 runtime 数据，调用方也直连 RO

**效果**：
- Gateway 职责更单一，不再做 internal 代理
- 调用方需知道 RO 地址，部署配置更复杂

---

## 四、推荐方案：方案 A + 验证

### 4.1 实施步骤

1. **清空转发前缀**
   ```python
   # helpers.py
   _RO_FORWARDED_PREFIXES = []  # 全部不转发
   ```

2. **验证 vm.py fallback**
   - 确认 Gateway 能访问 runtime 数据（共享 DB 或同步机制）
   - 测试 `GET /internal/runtimes/{id}/vm-tools` 在无转发时返回正确结果

3. **保留 client.forward 出站调用**
   - agent.py、subagent.py 中的 `client.forward` 不变
   - 用于 cancel-by-subagent、delete-by-subagent、runtimes/latest 等

### 4.2 可选：后续清理（方案 B 的简化版）

若方案 A 稳定运行，可逐步删除各文件中的 maybe_forward 调用，减少死代码。

---

## 五、影响范围

| 组件 | 影响 |
|------|------|
| Gateway | 不再转发入站请求，全部本地处理 |
| RO | 不再接收 Gateway 转发的 internal 请求；仍接收 agent.py/subagent.py 的 client.forward 调用 |
| Tools Server | 若调用 Gateway `/internal/runtimes/{id}/vm-tools`，改为由 Gateway 本地处理，需确保 Gateway 有 runtime 数据 |
| agent-runtime | 无影响（通常直连 RO 或 Gateway，不依赖 Gateway 转发） |

---

## 六、验收标准

1. `_RO_FORWARDED_PREFIXES` 为空或 maybe_forward 恒返回 None
2. `GET /internal/runtimes/{id}/vm-tools` 在 Gateway 本地返回正确结果
3. agent.py、subagent.py 的 cancel/delete 等仍能正确调用 RO
4. 相关单测、集成测试通过
