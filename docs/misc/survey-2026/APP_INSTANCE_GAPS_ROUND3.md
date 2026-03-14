# App Instance 边缘场景与改进建议（Round 3）

**输入**：`docs/survey-2026/APP_INSTANCE_ROUND1.md`、`docs/survey-2026/APP_INSTANCE_SYNC_ROUND2.md`

**产出日期**：2026-03-12

---

## 1. 缺口（Gaps）

### 1.1 app_instance 与 restoreSession 竞态

**现象**：`appInstanceId` 与 DeviceRegistry 中的 `app_instance_id` 存在**双重异步**，无强一致保证。

**根因**：

| 环节 | 实现 | 时序 |
|------|------|------|
| **get_app_instance** | `App.tsx` useEffect 内 `invoke('get_app_instance')`，fire-and-forget | App mount 后立即触发，与 restoreSession 并行 |
| **restoreSession** | `getAccessToken()` → `update_cloud_token` → `login_notify` → Cloud Bridge 连接 | 登录后触发，Cloud Bridge 需完成 WS 握手 |
| **DeviceRegistry 写入** | Cloud Bridge 握手时 `x-app-instance-id` header → `registry.connect(..., app_instance_id)` | 仅在 Cloud Bridge **已连接** 时 |

**竞态窗口**：

```
T0: App mount
    ├── useEffect #1: get_app_instance (异步)
    └── useEffect #2: restoreSession (异步)
         └── 登录成功 → update_cloud_token → login_notify
              └── Cloud Bridge 开始连接（需网络握手、relay 等）
                   └── WS 握手完成 → DeviceRegistry 写入 app_instance_id

T1: 用户登录后立即点「添加 Android」
    - appInstanceId: 可能已设置（get_app_instance 快）或仍 null（慢/失败）
    - DeviceRegistry: 大概率仍空（Cloud Bridge 连接通常需数百 ms～数秒）
```

**影响**：`resolveCurrentPcClientId(appInstanceId)` 在以下任一为真时失败或误选：

- `appInstanceId === null` → 直接 `return undefined`
- `appInstanceId` 有值但 `get_device_by_app_instance_id` 返回 None（Cloud Bridge 未连）→ 无 is_local，fallback 到 `devices[0]` 或 undefined

---

### 1.2 resolveCurrentPcClientId 失败提示

**现状**：AddAndroidModal、AddLinuxVMUserModal 在 `resolveCurrentPcClientId` 返回 `undefined` 时统一提示：

> **请选择目标 PC 或确保 Tauri 应用已连接**

**问题**：该提示覆盖多种根因，用户难以自助排查：

| 根因 | 表现 | 用户可采取的行动 |
|------|------|------------------|
| **A: appInstanceId 未同步** | get_app_instance 未完成或 invoke 失败（Web 模式） | 等待几秒重试 vs 确认是否为 Tauri 桌面端 |
| **B: Cloud Bridge 未连接** | DeviceRegistry 无 app_instance_id 匹配，无 is_local | 检查网络、等待 Cloud Bridge 重连 |
| **C: 设备列表为空** | 用户无 P2P 注册设备 | 先完成设备注册/绑定 |
| **D: 多 PC 无 is_local** | fallback 到 devices[0]，可能误选其他 PC | 需手动选择目标 PC |

**深层问题**：

- 前端无法区分 A/B/C/D，仅能拿到 `undefined`
- Gateway 侧 `get_device_by_app_instance_id` 返回 None 时无结构化错误码
- 建议：按根因分层提示，或提供「重试」「检查连接状态」等可操作指引

---

## 2. 边缘场景（Edge Scenarios）

### 2.1 登录后立即打开 Modal

**场景**：用户完成登录，界面刚显示「已登录」，立即点击「添加 Android 设备」或「添加 Linux 子用户」。

**时序**：

```
用户操作: 登录 → 立即点「添加 Android」
         │
         ├── restoreSession 可能仍在执行 getCurrentUser / update_cloud_token
         ├── Cloud Bridge 可能尚未收到 login_notify，或正在建立 WS
         └── get_app_instance 可能尚未返回（invoke 延迟）
```

**可能结果**：

1. **appInstanceId 为 null**：`resolveCurrentPcClientId(null)` → undefined → 提示「请选择目标 PC 或确保 Tauri 应用已连接」
2. **appInstanceId 有值但 DeviceRegistry 无匹配**：Cloud Bridge 未完成握手 → 无 is_local → fallback 到 devices[0]（多 PC 时可能选错）或 undefined
3. **两者均就绪**：正常（用户若稍等 1～2 秒再操作，概率较高）

**复现条件**：网络较慢、Tauri invoke 延迟、或用户操作极快时易触发。

---

### 2.2 Cloud Bridge 重连期间

**场景**：Cloud Bridge 因网络抖动、Gateway 重启等断开，进入 5 秒重连等待期。

**实现**（`cloud_bridge.rs`）：

```rust
loop {
    // connect_and_run 返回表示断开
    _ = connect_and_run(...) => {
        tracing::warn!("[CloudBridge] Disconnected from Gateway, retrying in 5s...");
    }
    tokio::time::sleep(Duration::from_secs(5)).await;
    // 重连...
}
```

**Gateway 侧**（`pc_client.py`）：

- `disconnect()` 仅置空 `device.ws`，DeviceState 保留
- `get_device_by_app_instance_id()` 要求 `d.is_connected`（即 `ws is not None`）

```python
# pc_client.py L163
if d.app_instance_id == aid and d.is_connected:
    return d
```

**重连期间行为**：

| 时间点 | DeviceRegistry | get_device_by_app_instance_id | is_local |
|--------|----------------|-------------------------------|----------|
| 断开瞬间 | device.ws = None | 返回 None（is_connected=false） | 无 |
| 重连等待 0～5s | 同上 | 同上 | 无 |
| 重连握手完成 | device.ws 恢复，app_instance_id 更新 | 命中 | 有 |

**影响**：

- 用户在重连窗口内打开 AddAndroidModal / AddLinuxVMUserModal
- `resolveCurrentPcClientId` 调用 `getMyDevices` → Gateway 查不到 is_local
- 退化为 `devices[0]`（多 PC 时可能选错）或 undefined
- 用户看到「请选择目标 PC 或确保 Tauri 应用已连接」，实际是**临时断线**，等待数秒即可恢复

**深层问题**：前端无 Cloud Bridge 连接状态，无法区分「从未连接」与「重连中」。

---

## 3. 改进建议

### 3.1 消除 app_instance 与 restoreSession 竞态

| 方案 | 描述 | 复杂度 |
|------|------|--------|
| **A: 串行化** | restoreSession 完成后再触发 get_app_instance，或反之；保证 appInstanceId 与 Cloud Bridge 就绪顺序 | 低 |
| **B: 依赖 login_notify** | 前端在「登录成功」回调中再请求 get_app_instance，此时 Cloud Bridge 已收到 login_notify，可减少竞态窗口 | 低 |
| **C: 轮询/重试** | Modal 打开时若 resolveCurrentPcClientId 失败，自动重试 2～3 次（间隔 500ms），给 Cloud Bridge 握手留时间 | 中 |
| **D: 就绪门控** | 新增 `app_instance_ready` 状态：仅当 get_app_instance 返回且 Cloud Bridge 已连接（需 Gateway 或 Tauri 暴露状态）时置 true；Modal 依赖此状态才允许操作 | 高 |

**推荐**：B + C 组合——登录成功后再取 appInstanceId，Modal 内对 resolveCurrentPcClientId 失败做短时重试。

---

### 3.2 改进 resolveCurrentPcClientId 失败提示

| 方案 | 描述 |
|------|------|
| **分层提示** | 根据可区分的条件给出不同文案：<br>• `appInstanceId === null` → 「应用实例未就绪，请稍候几秒后重试」<br>• `getMyDevices` 返回空列表 → 「暂无已注册设备，请先完成设备绑定」<br>• 有 devices 但无 is_local → 「当前 PC 未连接至云端，请检查网络或稍后重试」 |
| **结构化错误** | Gateway `getMyDevices` 或内部逻辑返回 `connection_status: "disconnected" | "reconnecting" | "unknown"`，前端据此展示 |
| **可操作指引** | 在通用提示下增加「重试」按钮，或「若问题持续，请检查：1) 网络连接 2) 是否为 Tauri 桌面端」 |

---

### 3.3 Cloud Bridge 重连期间体验

| 方案 | 描述 |
|------|------|
| **暴露连接状态** | Tauri 提供 `cloud_bridge_status: "connected" | "disconnected" | "reconnecting"`，前端据此在 Modal 或全局展示「连接恢复中，请稍候」 |
| **Modal 内重试** | resolveCurrentPcClientId 失败时，提示「云端连接恢复中，是否重试？」+ 重试按钮，避免用户误以为需手动选择 PC |
| **缩短重连间隔** | 将 5s 固定间隔改为指数退避（如 1s、2s、4s），首次重连更快，减少用户等待感 |

---

### 3.4 小结

| 缺口/场景 | 优先级 | 建议 |
|-----------|--------|------|
| app_instance 与 restoreSession 竞态 | 高 | 登录成功后再取 appInstanceId + Modal 内短时重试 |
| resolveCurrentPcClientId 失败提示 | 中 | 分层提示 + 可操作指引（重试、检查项） |
| 登录后立即打开 Modal | 高 | 同上，重试可缓解 |
| Cloud Bridge 重连期间 | 中 | 暴露连接状态 + Modal 内重试 |

---

## 附录：相关代码索引

| 模块 | 路径 |
|------|------|
| App.tsx get_app_instance / restoreSession | `novaic-app/src/App.tsx` L81-147 |
| resolveCurrentPcClientId | `novaic-app/src/services/api.ts` L1026-1035 |
| get_device_by_app_instance_id | `novaic-gateway/gateway/api/internal/pc_client.py` L157-165 |
| Cloud Bridge 重连循环 | `novaic-app/src-tauri/vmcontrol/src/cloud_bridge.rs` L147-166 |
| DeviceRegistry disconnect | `novaic-gateway/gateway/api/internal/pc_client.py` L129-154 |
| AddAndroidModal / AddLinuxVMUserModal | `novaic-app/src/components/VM/AddAndroidModal.tsx`、`AddLinuxVMUserModal.tsx` |
