# docs/UNIFIED_CURRENT_STATE_AND_RESEARCH.md 审核报告

## 三、AppInstance 与 my-devices 部分 — 逐条核对

---

### 1. AppInstance 字段：app_instance_id, app_type, machine_label, is_ready

**结论：正确**

| 字段 | 文档描述 | 代码验证 |
|------|----------|----------|
| app_instance_id | 本实例唯一 UUID，每次启动新建 | `state/mod.rs:47` — `pub app_instance_id: String`；`new_desktop/new_mobile` 使用 `uuid::Uuid::new_v4().to_string()` |
| app_type | Desktop / Mobile | `state/mod.rs:33-37` — `AppType` 枚举 `Desktop`, `Mobile`；`Serialize` 使用 `#[serde(rename_all = "lowercase")]` |
| machine_label | 机器型号/主机名 | `state/mod.rs:50` — `pub machine_label: String`；`device_info::machine_label()` |
| is_ready | 登录后为 true | `state/mod.rs:52` — `pub is_ready: bool`；`setup.rs:132` 登录后 `set_ready()` |

**代码位置**：`novaic-app/src-tauri/src/state/mod.rs:44-83`

---

### 2. 数据流：Tauri setup → Cloud Bridge WS → Gateway DeviceRegistry

**结论：正确（可补充细节）**

| 环节 | 代码位置 | 说明 |
|------|----------|------|
| Tauri setup | `setup.rs:53-60` | `AppInstance` 在 `setup_shared` 中创建并注入 |
| AppInstance → Cloud Bridge | `lib.rs:249-278` | 从 `AppInstanceState` 读取 `app_instance_id`、`machine_label`，传入 `CloudBridgeConfig` |
| Cloud Bridge WS | `vmcontrol/cloud_bridge.rs:174-201` | `connect_and_run` 在 WebSocket 握手时设置 `x-app-instance-id`、`x-machine-label` header |
| Gateway DeviceRegistry | `gateway/api/internal/pc_client.py:408-436` | WebSocket 端点 `/internal/pc/ws` 读取 header，调用 `registry.connect(..., app_instance_id=..., machine_label=...)` |

**补充**：Cloud Bridge 在 VmControl 子进程中运行，由 `lib.rs` 在 `setup_shared` 之后启动 VmControl 时传入配置。更精确的表述为：**Tauri 主进程（含 setup）→ VmControl Cloud Bridge WS → Gateway DeviceRegistry**。

---

### 3. my-devices 来源：_p2p_registry + DeviceRegistry

**结论：正确**

| 来源 | 代码位置 | 说明 |
|------|----------|------|
| _p2p_registry | `gateway/api/p2p.py:59, 341-344` | P2P 心跳注册的 `P2PEntry`（device_id, user_id, ext_addr, online 等） |
| DeviceRegistry | `gateway/api/p2p.py:320-325` | `_build_device_item` 中 `registry.get_device(entry.device_id)` 补充 `app_instance_id`、`machine_label` |

合并逻辑：遍历 `_p2p_registry.values()`，对每个 entry 调用 `_build_device_item(entry, registry, current_device_id=...)`，从 DeviceRegistry 补充 Cloud Bridge 上报的 app_instance 信息。

**代码位置**：`novaic-gateway/gateway/api/p2p.py:306-344`

---

### 4. 返回结构：{ devices, by_app_instance }

**结论：正确**

| 字段 | 代码位置 | 结构 |
|------|----------|------|
| devices | `p2p.py:341-344, 366` | `result` 为 flat list，每项含 device_id, ext_addr, online, last_seen, is_local, app_instance_id, machine_label |
| by_app_instance | `p2p.py:347-364, 367` | `list(by_app_instance.values())`，每项为 `{ app_instance_id, machine_label, devices: [...] }` |

**代码位置**：`novaic-gateway/gateway/api/p2p.py:366-368`

```python
return {
    "devices": result,
    "by_app_instance": list(by_app_instance.values()),
}
```

---

### 5. is_local 需 current_device_id 参数，get_vnc_proxy_url、vnc_bridge_connect 是否未传

**结论：正确 — 文档描述的 Gap 属实**

| 调用方 | 代码位置 | 是否传 current_device_id |
|--------|----------|--------------------------|
| get_vnc_proxy_url | `vnc_urls.rs:39-40` | **未传** — `gateway_get_impl(&url, &token, "/api/p2p/my-devices")` 无 query |
| get_scrcpy_proxy_url | `vnc_urls.rs:88-89` | **未传** — 同上 |
| vnc_bridge_connect | `vnc_bridge.rs:49-50` | **未传** — `gateway_get_impl(&url, &token, "/api/p2p/my-devices")` 无 query |

Gateway 端：`p2p.py:329` 定义 `current_device_id: str = ""` 为 query 参数；`p2p.py:315-316` 仅在 `current_device_id and entry.device_id == current_device_id` 时设置 `item["is_local"] = True`。

**结论**：上述调用方均未传入 `current_device_id`，`is_local` 实际未生效。

**修正建议**：在 `vnc_urls.rs` 和 `vnc_bridge.rs` 中，当 `local_vmcontrol` 有值时，先调用 `get_local_device_id` 获取本机 device_id，再构造 path：`/api/p2p/my-devices?current_device_id={device_id}`。但当前这些调用仅用于解析目标 device_id（取第一个 online），不用于 UI 展示，因此 `is_local` 未传对功能影响有限；若前端需展示「本机」标签，应在前端单独调用 `gateway_get("/api/p2p/my-devices?current_device_id=" + localId)`。

---

## 汇总

| 条目 | 结论 | 备注 |
|------|------|------|
| 1. AppInstance 字段 | 正确 | 四个字段均与代码一致 |
| 2. 数据流 | 正确 | 可补充「VmControl 子进程」细节 |
| 3. my-devices 来源 | 正确 | _p2p_registry + DeviceRegistry 合并 |
| 4. 返回结构 | 正确 | 含 devices 与 by_app_instance |
| 5. current_device_id 未传 | 正确 | get_vnc_proxy_url、vnc_bridge_connect 均未传 |

---

## 附录：关键代码位置索引

| 文件 | 行号 | 用途 |
|------|------|------|
| novaic-app/src-tauri/src/state/mod.rs | 44-83 | AppInstance 定义 |
| novaic-app/src-tauri/src/setup.rs | 53-60, 126-135 | AppInstance 创建、ready 任务 |
| novaic-app/src-tauri/src/lib.rs | 249-278 | 传入 CloudBridgeConfig |
| novaic-app/src-tauri/vmcontrol/src/cloud_bridge.rs | 174-201 | WS header x-app-instance-id, x-machine-label |
| novaic-gateway/gateway/api/internal/pc_client.py | 408-436, 551-552 | WebSocket 握手、DeviceRegistry.connect |
| novaic-gateway/gateway/api/p2p.py | 306-368 | _build_device_item、my-devices 端点 |
| novaic-app/src-tauri/src/commands/vnc_urls.rs | 39-40, 88-89 | gateway_get_impl 无 current_device_id |
| novaic-app/src-tauri/src/commands/vnc_bridge.rs | 49-50 | gateway_get_impl 无 current_device_id |
