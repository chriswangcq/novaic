# Maindesk vs Subuser 差异（VmControl P2P Server 之前）

> 在请求到达 P2P Server 的 `handle_incoming_stream` 之前，前端 + Tauri 层仍存在的差异。

---

## 一、边界说明

**「P2P Server 前」** = 以下链路结束于 `open_vnc_stream` 发送 QUIC 流头部：

```
DeviceDesktopView → createVncTransport → vnc_stream_connect → route_vnc_to_channel → open_vnc_stream
                                                                                        │
                                                                                        └─ 发送 [0x01][id_len][resource_id]
                                                                                            ↓
                                                                                    P2P Server 收到
                                                                                    handle_incoming_stream
                                                                                    ensure_vnc_endpoint  ← 此处开始有 maindesk/subuser 分支
```

---

## 二、P2P Server 前的差异清单

### 2.1 DeviceDesktopView（前端）

| 维度 | Maindesk | Subuser |
|------|----------|---------|
| **Props** | `subjectType: 'main'\|'default'`, `device: Device` | `subjectType: 'vm_user'`, `deviceId`, `username`, `displayNum` |
| **vncTarget.resourceId** | `deviceId` | `deviceId:username` |
| **deviceStatus** | 拉取 `api.devices.status`，必须 `running` 才建连 | 不拉取，无前置条件 |
| **建连条件** | `vncTarget && deviceStatus==='running'` | `vncTarget` 存在即可 |
| **Start/Stop** | 有按钮，可启停 VM | 无 |
| **非 running 时 UI** | 显示 Start 按钮 / Starting / Stopped | 直接显示 VNC canvas（无 running 检查） |

**文件**：`DeviceDesktopView.tsx`

---

### 2.2 中间件（vncBridge → tunnel）

**已完全统一**：无 maindesk/subuser 分支。tunnel 通过 HTTP POST vmcontrol `/api/vms/vnc-endpoint` 解析 socket，差异在 vmcontrol 的 `vnc_endpoint.rs`。

---

## 三、差异汇总表

| 层级 | 差异项 | 可否统一 |
|------|--------|----------|
| **DeviceDesktopView** | deviceStatus 拉取 + 前置条件 | 可：subuser 也拉 status，或 maindesk 放宽 |
| **DeviceDesktopView** | Start/Stop UI | 不可：subuser 无 VM 启停 |
| **DeviceDesktopView** | resourceId + username | resourceId=vm_id，username maindesk="" subuser=实际 |
| **vncTransport** | timeout | 已统一 60s |

---

## 四、可统一的方向

1. **deviceStatus 前置**：subuser 也可拉 `api.devices.status`，只有 VM running 才建连，减少「Xvnc 未就绪」时的失败。
2. **timeout**：统一为 60s，或按 `resourceId.includes(':')` 保持现状（subuser 更久）。
3. **resourceId**：保持 `deviceId` vs `deviceId:username`，这是协议约定，不能改。

---

## 五、不可统一的部分

- **Start/Stop**：subuser 无 VM 启停，Xvnc 由 VM 内 systemd 管理。

---

*文档基于 2026-03 代码库*
