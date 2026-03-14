# VNC 问题定位报告：Maindesk 连不上 + 频繁切换不稳定

> **仅分析定位，不修改任何代码。**

---

## 一、问题 1：Maindesk 连不上，Subuser 可以连上

### 1.1 根因：Maindesk 无轮询，Subuser 有 30s 轮询

| 类型 | ensure_vnc_endpoint 行为 | 重试 |
|------|--------------------------|------|
| **Maindesk** | 单次查找 `novaic-vnc-{resource_id}.sock`，不存在即失败 | tunnel 层 3 次 × 200ms ≈ 600ms |
| **Subuser** | 轮询 port 文件 `/tmp/novaic/share-{vm_id}/vnc-{username}.port` 最多 30s | 每 500ms 检查一次 |

**代码位置**：
- `p2p/src/vnc_endpoint.rs` 112–128 行：maindesk 分支，无轮询
- `p2p/src/vnc_endpoint.rs` 131–213 行：subuser 分支，30s 轮询
- `p2p/src/tunnel.rs` 101–128 行：`VNC_RETRY_ATTEMPTS=3`，`VNC_RETRY_DELAY_MS=200`

### 1.2 时序竞态（Maindesk）

1. 用户启动 VM → Gateway → VmControl → QEMU
2. `deviceStatus` 变为 `running` 时 VM 进程已存在
3. QEMU 创建 VNC socket 可能晚于进程就绪
4. 前端在 `deviceStatus === 'running'` 时创建 transport
5. `ensure_vnc_endpoint` 若在 socket 创建前执行 → 失败
6. 3 次 × 200ms 共约 600ms，若 QEMU 更慢则仍失败

Subuser 能连上，是因为有 30s 轮询，能等到 port 文件出现。

### 1.3 可能的 resource_id 不一致（待验证）

- **Maindesk**：`resourceId = device_id`（来自 `bindingToVncTarget`）
- **VM socket**：`novaic-vnc-{agent_id}.sock`（vm.rs 497 行）
- 若 `device_id !== agent_id`，会查找错误路径

**验证方式**：在 `ensure_vnc_endpoint` 失败时打日志，确认 `resource_id` 与 `/tmp/novaic/` 下实际 socket 文件名是否一致。

### 1.4 其他可能

- `temp_dir()` 优先于 `/tmp/novaic`：若 `$TMPDIR/novaic/` 有旧 socket，可能连到已关闭的 VM
- `p.exists()` 与 `UnixStream::connect` 之间的竞态：检查时存在，连接时已被删除

---

## 二、问题 2：频繁切换 device 时连接不稳定

### 2.1 流程概览

```
用户切换 device/agent
    → vncTargetKey 变化
    → useEffect 触发 createVncTransport(newTarget)
    → 若 cache 命中且 OPEN：复用
    → 否则：新建 transport，connect()
    → setTransport(newTransport)
    → useVnc effect → doConnect()
        → prevTransport.close()  // 关闭旧 transport
        → new RFB(container, newTransport)
```

### 2.2 潜在竞态

| 场景 | 风险 |
|------|------|
| **快速连续切换** | `createVncTransport` 尚未 resolve，用户已再次切换；旧请求结果可能覆盖新 target 的 transport |
| **requestId 校验** | 仅保证“最新请求覆盖”，不保证“旧请求不会误覆盖” |
| **cache 复用** | 切换 device 时 key 变化，会新建 transport；但若短时间内切回原 device，可能复用已关闭的 cache 条目（readyState !== OPEN 时会删除并重建） |
| **doConnect 关旧开新** | 每次 transport 变化都会关闭 prevTransport；快速切换时可能连续关闭多个连接 |

### 2.3 相关代码

- `AgentDesktopView.tsx`：`vncTargetKey`、`requestIdRef`、`createVncTransport`
- `useVnc.ts`：`doConnect` 中 `prevTransport.close()`
- `vncTransport.ts`：`transportCache`，key 为 `resourceId|pcClientId`

### 2.4 切换时的组件行为

- **Agent 切换**：同一 `AgentDesktopView` 实例，仅 props 变化
- **Device 切换（同类型）**：props 更新，一般不 unmount
- **Main ↔ vm_user 切换**：可能 unmount + remount（不同组件）
- **Tab 切换（devices ↔ chat）**：unmount

---

## 三、定位结论汇总

### 问题 1：Maindesk 连不上

| 根因 | 置信度 | 说明 |
|------|--------|------|
| Maindesk 无轮询，仅 3×200ms 重试 | 高 | 与 subuser 行为差异明显，易产生时序竞态 |
| resource_id (device_id) 与 socket 名 (agent_id) 不一致 | 中 | 需结合实际 binding 与 VM 启动逻辑验证 |
| temp_dir 优先导致连到旧 socket | 低 | 仅在特定环境可能发生 |

### 问题 2：频繁切换不稳定

| 根因 | 置信度 | 说明 |
|------|--------|------|
| 快速切换时 createVncTransport 竞态 | 中 | requestId 可缓解，但无法完全消除 |
| 每次切换都关旧开新，连接抖动 | 中 | doConnect 设计如此，快速切换会放大 |
| cache 在切换时可能短暂失效 | 低 | 不同 key 会新建，逻辑正常 |

---

## 四、建议的修复方向（供后续实现参考）

1. **Maindesk**：在 `ensure_vnc_endpoint` 的 maindesk 分支增加轮询（如 10–15s，500ms 间隔），与 subuser 行为对齐
2. **resource_id**：确认 maindesk 场景下 `device_id` 与 VM socket 使用的 id 是否一致，必要时改为使用 `agent_id`
3. **切换稳定性**：对 `createVncTransport` 做防抖或取消过期请求，减少快速切换时的竞态
