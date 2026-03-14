# Maindesk vs Subuser 差异审计

> 目标：中间件（vncBridge → tunnel）完全无分支，差异仅在前端业务逻辑和 vmcontrol
> **已实现**（2026-03）

---

## 一、差异分布（实现后）

### 1.1 中间件链（已无分支）

| 层级 | 文件 | 状态 |
|------|------|------|
| vncBridge | vncBridge.ts | 无分支 |
| vncTransport | vncTransport.ts | 无分支 |
| vnc_stream | vnc_stream.rs | pool_key 统一 `format!("{}:{}", vm_id, username)` |
| vnc_proxy | vnc_proxy.rs | 无分支 |
| tunnel | tunnel.rs | 无分支，HTTP POST vmcontrol 解析 endpoint |
| p2p | vnc_endpoint 已移除 | 逻辑迁入 vmcontrol |

### 1.2 vmcontrol（应有差异）

| 文件 | 差异 | 说明 |
|------|------|------|
| vnc_endpoint.rs（新建） | maindesk/subuser socket 解析 | 从 p2p 迁入 |
| vnc.rs | URL 解析 resource_id | 保持 |
| vm.rs | QEMU 启动、subuser port、shutdown_proxy_for_vm | 保持 |

### 1.3 前端（应有差异）

| 组件 | 差异 | 说明 |
|------|------|------|
| DeviceDesktopView | Props、Start/Stop、vncTarget 构造 | maindesk 有 device+status，subuser 有 username |
| useDeviceVncTarget | resourceId + username | 已统一格式 |
| useAgentDevice | bindingToVncTarget | 已统一格式 |

---

## 二、实现方案

### 2.1 中间件统一

1. **vnc_stream pool_key**：`format!("{}:{}", vm_id, username)` 统一，maindesk 时 username="" → "vm_id:"
2. **ensure_vnc_endpoint**：从 p2p 移至 vmcontrol
3. **tunnel**：改为调用 vmcontrol HTTP `POST /api/vms/vnc-endpoint`，不再直接调用 p2p

### 2.2 vmcontrol 新增

- **POST /api/vms/vnc-endpoint**：`{ "vm_id": "...", "username": "..." }` → `{ "socket_path": "/tmp/novaic/..." }`
- **vmcontrol/src/vnc_endpoint.rs**：从 p2p 迁入 ensure_vnc_endpoint、shutdown_proxy_for_vm

### 2.3 p2p 精简

- 移除 `vnc_endpoint` 模块（或仅保留 MAX_RESOURCE_ID_LEN 常量供 tunnel 解析用）
- tunnel 通过 HTTP 解析 endpoint，不再依赖 p2p::vnc_endpoint

---

## 三、数据流（统一后）

```
前端 VncTarget(resourceId, username)
    ↓ 无分支
vncBridge → vnc_stream_connect(resourceId, username)
    ↓ 无分支（pool_key = "vm_id:username" 统一格式）
route_vnc_to_channel → open_vnc_stream(vm_id, username)
    ↓ 无分支
QUIC [vm_id][username]
    ↓ 无分支
tunnel handle_incoming_stream
    ↓ 无分支：HTTP POST vmcontrol /api/vms/vnc-endpoint
vmcontrol vnc_endpoint.ensure_vnc_endpoint(vm_id, username)  ← 唯一分支在此
    ↓
Unix socket path → proxy_quic_to_unix
```

---

*2026-03 审计*
