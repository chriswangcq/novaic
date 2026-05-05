# WebRTC 统一远程桌面

> 对应 `**HANDOVER.md` §9**。实现位于 `**novaic-app/src-tauri/vmcontrol/`**。

## 统一入口

所有设备类型走 **WebRTC**，前端主要传 `device_id`：

```
useWebRtc → invoke('send_webrtc_offer') / AppBridge WS
  → Gateway 中继（注入 TURN ice_servers）
  → CloudBridge WS → VmControl cloud_bridge.rs
      → /api/webrtc/start → webrtc_unified.rs
      → DeviceKind 分发：
           linux_vm   → webrtc_vm.rs  (frame capture → H.264)
           android    → webrtc_scrcpy.rs
           host_desktop → webrtc_hd.rs (屏幕采集)
```

前端只面对统一 WebRTC 渲染面。

## 信令（方案 B）

**Offer / Answer / ICE 候选**同一条 **AppBridge WS**，保证有序、减少竞态。

## Device Registry

VmControl 通过 Device Service CloudBridge 接收设备同步消息，并写入本地
**vmcontrol.db**（sqlx）。

## 编码（摘要）

- 优先级：**VideoToolbox**（GPU）→ FFmpeg → openh264。
- 含 BGRA 直编码、码率上限、VT 失败降级、keyframes 与 **Anti-Slowmo** 等优化（见 HANDOVER §9.4）。

## Scrcpy 多客户端

每 `device_serial` 一个 **ScrcpyBroadcaster**，单 TCP 连接 + `broadcast` 分发给多订阅者。

## 前端操控台（速查）


| 区域     | 代表文件                                     |
| ------ | ---------------------------------------- |
| 主控制台   | `DeviceConsole.tsx`、`ConsoleToolbar.tsx` |
| 虚拟键盘   | `VirtualKeyboard.tsx`                    |
| 缩放/平移  | `useViewTransform.ts`                    |
| WebRTC | `useWebRtc.ts`                           |
| 远程输入   | `useRemoteInput.ts`                      |


## Rust 速查


| 需求               | 文件                                               |
| ---------------- | ------------------------------------------------ |
| 统一路由             | `vmcontrol/src/api/routes/webrtc_unified.rs`     |
| Device DB        | `vmcontrol/src/db/device_repo.rs`                |
| HD / VM / Scrcpy | `webrtc_hd.rs`、`webrtc_vm.rs`、`webrtc_scrcpy.rs` |
| VT 编码            | `vmcontrol/src/webrtc/vt_encoder.rs`             |
| Peer             | `vmcontrol/src/webrtc/peer.rs`                   |
| 键盘（CGEvent）      | `vmcontrol/src/input/handler.rs`                 |


## 相关

- [thin-client-and-topology.md](thin-client-and-topology.md) — TURN  
- [realtime-sync.md](realtime-sync.md) — AppBridge WS
