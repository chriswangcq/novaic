# WebRTC 显示管线

本文档描述 Novaic 平台中 WebRTC 显示管线的完整架构，涵盖信令流程、视频编码、Broadcaster 设计、DataChannel 输入管线以及不同设备类型的差异化处理。

## 管线总览

```
┌──────────┐     ┌──────────────┐     ┌──────────┐     ┌───────────┐     ┌────────────┐
│   App    │────►│  AppBridge   │────►│ Gateway  │────►│  Device   │────►│ VmControl  │
│ (React)  │ WS  │   WS :19999 │     │  :19999  │     │  :19993   │ WS  │  (Rust)    │
└──────────┘     └──────────────┘     └──────────┘     └───────────┘     └──────┬─────┘
                                                                                │
                                       WebRTC PeerConnection                    │
                      ◄─────────────────────────────────────────────────────────┘
                        video track (H.264) + audio track (Opus)
                        + DataChannel (input events JSON)
```

## 信令流程

WebRTC 会话建立的信令通过 HTTP 完成：

| 步骤 | 方向 | 内容 |
|------|------|------|
| 1 | App → Gateway | POST `/api/webrtc/start` with `{ device_id, sdp_offer }` |
| 2 | Gateway → Device Service | 代理转发请求 |
| 3 | Device Service → VmControl | 通过 WS typed command 转发 |
| 4 | VmControl | 创建 PeerConnection，设置远端 SDP |
| 5 | VmControl → Device Service | 返回 `sdp_answer` |
| 6 | Device Service → Gateway → App | SDP Answer 返回 |
| 7 | 双向 | Trickle ICE candidates 交换（通过同一 HTTP 通道） |

VmControl 提供统一的 WebRTC 入口：`POST /api/webrtc/start`，接受标准 SDP offer，屏蔽设备类型差异。

## 视频编码

### DeviceKind 路由

VmControl 根据 DeviceKind 选择不同的视频源和编码路径：

| DeviceKind | 视频源 | 编码格式 | 采集方式 |
|------------|--------|---------|---------|
| `LinuxVm` | VNC 帧缓冲 | H.264 | RFB 协议连接 VNC Server → 帧解码 → 编码 |
| `Android` | scrcpy 视频流 | H.264 | scrcpy server 3.3.4 推送 → 解复用 |
| `HostDesktop` | 屏幕采集 | H.264 | 系统屏幕捕获 API → 帧编码 |

### 编码器选择

| 编码器 | 平台 | 类型 | 说明 |
|--------|------|------|------|
| openh264 | 全平台 | 软件 | 默认 fallback，兼容性最佳 |
| VideoToolbox | macOS | 硬件 | Apple 硬件加速，低功耗 |
| VA-API | Linux | 硬件 | Intel/AMD GPU 加速 |
| NVENC | Linux | 硬件 | NVIDIA GPU 加速 |

编码器通过 FFmpeg 抽象层统一接口，运行时按优先级自动探测可用编码器。

## Broadcaster 架构

VideoBroadcaster 实现一个视频源到多个 WebRTC peer 的广播：

```
                          ┌──────────────────┐
                          │   Video Source    │
                          │ (VNC/scrcpy/屏幕) │
                          └────────┬─────────┘
                                   │ 原始帧
                                   ▼
                          ┌──────────────────┐
                          │  VideoBroadcaster │
                          │                  │
                          │  4-frame buffer  │  ◄── 低延迟设计
                          │  (环形缓冲区)     │
                          │                  │
                          │  30s idle 自动停止│  ◄── 资源节约
                          │  lazy creation   │  ◄── 按需创建
                          └──┬─────┬─────┬───┘
                             │     │     │
                        ┌────▼┐ ┌──▼──┐ ┌▼────┐
                        │Peer│ │Peer │ │Peer │
                        │ A  │ │ B   │ │ C   │
                        └────┘ └─────┘ └─────┘
```

核心设计要素：

| 特性 | 说明 |
|------|------|
| **Lazy Creation** | 首个 peer 连接时才创建 Broadcaster 和启动视频源 |
| **4-frame Buffer** | 环形缓冲区保留最近 4 帧，新 peer 可立即获得画面（低延迟） |
| **30s Idle Auto-stop** | 最后一个 peer 断开后 30 秒无新连接则停止采集，释放资源 |
| **One Source → N Peers** | 视频源只采集/编码一次，通过 RTP 分发给所有 peer |

### Peer 管理

```
全局注册表: PEERS: DashMap<PeerId, PeerState>

每个 PeerState 包含：
  - PeerConnection 实例
  - 关联的 device_id
  - DataChannel 引用
  - ICE 连接状态

全局 UDP 复用: UDPMux
  - 所有 peer 共享同一个 UDP socket
  - 减少端口占用和系统资源消耗
  - Trickle ICE 逐步收集 candidate
```

## DataChannel 输入管线

用户的鼠标、键盘等输入事件通过 WebRTC DataChannel 传输到设备，采用 JSON 协议格式。

### 输入事件 JSON 示例

```json
{ "type": "mouse_move", "x": 512, "y": 384 }
{ "type": "mouse_click", "x": 512, "y": 384, "button": "left" }
{ "type": "key_press", "key": "Enter" }
{ "type": "scroll", "x": 512, "y": 384, "delta_x": 0, "delta_y": -120 }
```

### 按设备类型的适配器

DataChannel 接收到 JSON 事件后，通过 per-target adapter 转换为设备特定协议：

| 适配器 | 目标设备 | 转换目标 |
|--------|---------|---------|
| **Pc / enigo** | HostDesktop | enigo 库系统级鼠标/键盘事件 |
| **Android / scrcpy** | Android | scrcpy binary control message（坐标+触摸事件） |
| **LinuxVm / RFB** | Linux VM | RFB 协议 PointerEvent / KeyEvent |
| **Passthrough / SPICE** | SPICE 设备 | SPICE 输入通道消息 |

## 设备类型差异

| 设备类型 | 视频采集 | 输入注入 | 特殊说明 |
|---------|---------|---------|---------|
| LinuxVm | RFB/VNC 帧缓冲 → RGB → H.264 | RFB PointerEvent / KeyEvent | 通过 VNC Server 连接 |
| Android | scrcpy 3.3.4 H.264 裸流 → 解复用 | scrcpy binary control message | tunnel_forward 协议，首 12 字节 metadata |
| HostDesktop | 系统屏幕捕获 → H.264 | enigo 系统级事件 | macOS: SCScreenshotManager, Linux: PipeWire/X11 |

### 音频与光标

- **音频**：cpal 跨平台采集 → Opus 编码 → WebRTC audio track
- **光标**：独立 JSON 数据流传输光标形状和位置，不烘焙到视频帧中，客户端可自定义渲染
