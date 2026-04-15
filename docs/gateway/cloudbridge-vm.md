# CloudBridge WS — Device Service ↔ VmControl 通信

> 更新：2026-04-15（硬切完成后）
> 硬切设计文档：[../architecture/cloudbridge-vmcontrol-hard-cut.md](../architecture/cloudbridge-vmcontrol-hard-cut.md)

## 1. 架构现状

CloudBridge WS 是 **Device Service** (`:19993`) 与用户 PC 上的 **VmControl** (Rust) 之间的长连接通道。

```
App → Gateway (AppWS signaling) → Device Service → CloudBridge (typed WS) → VmControl
```

关键边界：

- **Gateway** 只负责 App 信令（WebRTC offer/answer/ICE）转发和 TURN 凭证注入，不拥有 CloudBridge
- **Device Service** 拥有 CloudBridge WS (`/internal/pc/ws`)，作为设备路由和 typed command broker
- **VmControl** 是唯一 runtime owner，负责 VM/WebRTC/输入控制/截图等全部执行

## 2. 协议

CloudBridge 采用 **typed WebSocket protocol**，每条消息都有明确的 `type` 字段。

### Device Service → VmControl 命令

```json
{ "type": "vm_list", "request_id": "uuid" }
{ "type": "vm_get", "request_id": "uuid", "vm_id": "agent-1" }
{ "type": "vm_start", "request_id": "uuid", "vm_id": "agent-1", "payload": { ... } }
{ "type": "vm_stop", "request_id": "uuid", "vm_id": "agent-1" }
{ "type": "vm_restart", "request_id": "uuid", "vm_id": "agent-1" }
{ "type": "vm_screenshot", "request_id": "uuid", "vm_id": "agent-1" }
{ "type": "vm_input_keys", "request_id": "uuid", "vm_id": "agent-1", "payload": { ... } }
{ "type": "webrtc_offer", "device_id": "dev-1", "session_id": "sess-1", "sdp_offer": "..." }
{ "type": "webrtc_stop", "device_id": "dev-1", "session_id": "sess-1" }
```

### VmControl → Device Service 结果 / 事件

```json
{ "type": "command_result", "request_id": "uuid", "ok": true, "result": { ... } }
{ "type": "command_error", "request_id": "uuid", "error": { "code": "vm_not_found", "message": "..." } }
{ "type": "webrtc_answer", "device_id": "dev-1", "session_id": "sess-1", "sdp_answer": "..." }
{ "type": "ice_candidate", "device_id": "dev-1", "session_id": "sess-1", "candidate": { ... } }
{ "type": "vm_status_report", "vm_ids": [ ... ], "android_serials": [ ... ] }
```

## 3. 代码位置

| 职责 | 文件 |
|------|------|
| CloudBridge WS 服务端 + typed command broker | `novaic-device/device/pc_client.py` |
| CloudBridge WS 客户端 + typed command dispatch | `novaic-app/src-tauri/vmcontrol/src/cloud_bridge.rs` |
| App 信令 (WebRTC relay) | `novaic-gateway/gateway/api/app_client.py` |
| Northbound VM API | `novaic-device/device/vm_routes.py`, `vmcontrol_routes.py` |
| Gateway → Device 内部 API | `novaic-device/device/gateway_facing_api.py` |
| Agent tool proxy | `novaic-device/device/agent_vm_proxy.py` |

## 4. 已删除的历史能力

以下内容已在 2026-04-15 硬切中删除：

- `proxy_request` / `proxy_response`（HTTP-over-WS 桥协议）
- `gateway_url` fallback（VmControl 不再尝试连接 Gateway）
- `VmManager` / 本地 QEMU 生命周期
- VNC 路径（`/vnc` WS proxy、`vnc_url`、`restart_vnc`）
- `legacy-*` device id fallback
- `user_id="local"` fallback
