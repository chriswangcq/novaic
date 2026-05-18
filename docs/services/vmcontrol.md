# VmControl

## 概述与职责

VmControl 是 Novaic 平台的设备控制核心，以独立 Rust workspace crate 的形式存在于 `novaic-app/src-tauri/vmcontrol/` 目录下。它负责 WebRTC 视频流管理、设备命令下发、屏幕投射和输入转发，是 Agent 和用户与设备交互的底层引擎。

核心职责包括：

- 统一的 WebRTC 视频流连接管理
- Scrcpy 协议集成（Android 设备）
- Cloud Bridge 类型化命令通信
- 多设备类型的统一入口
- DataChannel 输入管道

## 嵌入式服务架构

VmControl 支持两种运行模式，适应不同的部署场景：

### 嵌入式模式（Library）

| 属性 | 说明 |
|------|------|
| 运行方式 | 作为 Rust 库嵌入到 Tauri 桌面应用中 |
| 网络端口 | 无独立 HTTP 端口 |
| 调用方式 | 通过 `Router::oneshot()` 进行零网络开销的函数调用 |
| 适用场景 | 桌面客户端本地运行 |

### 独立二进制模式（Standalone）

| 属性 | 说明 |
|------|------|
| 运行方式 | 独立的 HTTP 服务进程 |
| 网络端口 | `:19992` |
| 调用方式 | 标准 HTTP API 调用 |
| 适用场景 | 云端部署、无头模式 |

两种模式共享同一套 axum Router 定义。嵌入式模式通过 `Router::oneshot()` 方法将 HTTP 请求直接在进程内路由，跳过网络栈，实现零延迟调用。

```
嵌入式模式                        独立二进制模式
┌────────────────┐              ┌────────────────┐
│  Tauri App     │              │  HTTP Server   │
│  ┌──────────┐  │              │  (:19992)      │
│  │ VmControl│  │              │  ┌──────────┐  │
│  │ (Library) │  │              │  │ VmControl│  │
│  └──────────┘  │              │  │ (Binary)  │  │
│  Router::      │              │  └──────────┘  │
│  oneshot()     │              │  axum::serve() │
└────────────────┘              └────────────────┘
      │                               │
      └─── 共享 axum Router ────────┘
```

## WebRTC 连接管理

VmControl 实现了完整的 WebRTC 连接管理，核心组件是 VideoBroadcaster。

### VideoBroadcaster

VideoBroadcaster 实现 "一源多投" 模式：一个 H.264 视频源可以同时向 N 个 WebRTC Peer 分发视频流。

| 特性 | 说明 |
|------|------|
| 视频编码 | H.264 |
| 分发模型 | 1 Source → N Peers |
| 网络复用 | 全局 UDPMux，所有 Peer 共享同一 UDP 端口 |
| ICE 策略 | Trickle ICE，渐进式候选交换 |

### 连接建立流程

```
客户端                   VmControl                  设备
  │                         │                         │
  │── Offer SDP ──────────►│                         │
  │                         │── 建立视频源连接 ────────►│
  │                         │◄── H.264 视频流 ────────│
  │◄── Answer SDP ─────────│                         │
  │                         │                         │
  │◄── ICE Candidate ──────│                         │
  │── ICE Candidate ──────►│                         │
  │                         │                         │
  │◄═══ WebRTC 视频流 ═════│◄═══ H.264 源 ══════════│
```

### 统一入口

WebRTC 连接通过 DeviceKind 统一入口，根据设备类型自动选择底层协议：

| DeviceKind | 视频源 | 说明 |
|------------|--------|------|
| `LinuxVm` | VNC / SPICE | 从 Linux VM 获取桌面视频流 |
| `Android` | Scrcpy | 通过 Scrcpy 协议获取 Android 屏幕流 |
| `HostDesktop` | 本地桌面捕获 | 捕获宿主机桌面 |

## Scrcpy 集成

VmControl 集成了 Scrcpy 3.3.4 的 `tunnel_forward` 协议，用于 Android 设备的屏幕镜像和控制：

### 协议流程

```
VmControl                          Android 设备
   │                                    │
   │── ADB forward 端口映射 ──────────►│
   │                                    │
   │── TCP 连接到 scrcpy-server ──────►│
   │◄── 设备信息（分辨率、旋转等） ─────│
   │                                    │
   │◄── H.264 视频帧 ─────────────────│  视频通道
   │── 控制命令（触摸、按键） ────────►│  控制通道
```

### 集成特性

| 特性 | 说明 |
|------|------|
| Scrcpy 版本 | 3.3.4 |
| 传输模式 | `tunnel_forward`（服务端监听，客户端连接） |
| 视频编码 | H.264 硬件编码（设备端） |
| 控制协议 | Scrcpy 自定义二进制控制协议 |
| 双通道 | 视频和控制分离为独立的 TCP 连接 |

## Cloud Bridge 协议

Cloud Bridge 是 VmControl 与 Device 服务之间的通信层，通过 WebSocket 实现 30 种类型化命令的双向通信：

### 连接方式

VmControl 作为 WebSocket 客户端连接到 Device 服务的 `/internal/pc/ws` 端点。

### 命令分类

| 类别 | 命令示例 | 说明 |
|------|----------|------|
| 鼠标操作 | `mouse_move`, `mouse_click`, `mouse_scroll` | 鼠标位移、点击、滚轮 |
| 键盘操作 | `key_press`, `key_release`, `text_input` | 按键和文本输入 |
| 屏幕操作 | `screenshot`, `screen_info` | 截屏和屏幕信息获取 |
| 文件操作 | `file_upload`, `file_download`, `file_list` | 文件传输 |
| 进程操作 | `process_start`, `process_kill` | 进程管理 |
| 系统操作 | `system_info`, `clipboard_get`, `clipboard_set` | 系统级操作 |

### 消息格式

```json
{
  "command_type": "mouse_click",
  "command_id": "cmd_abc123",
  "payload": {
    "x": 500,
    "y": 300,
    "button": "left",
    "click_type": "single"
  }
}
```

## 设备类型统一

VmControl 通过 DeviceKind 枚举统一了三种设备类型的控制接口：

### DataChannel 输入管道

WebRTC DataChannel 承载了实时输入事件，支持 4 种目标类型：

| Target 类型 | 说明 | 输入转发方式 |
|-------------|------|-------------|
| `Pc` | 通用 PC 类设备 | 通过 Cloud Bridge WS 命令 |
| `Android` | Android 设备 | 通过 Scrcpy 控制通道 |
| `LinuxVm` | Linux 虚拟机 | 通过 VNC/SPICE 输入协议 |
| `Passthrough` | 透传模式 | 直接转发原始输入事件 |

DataChannel 输入管道将前端的鼠标、键盘和触摸事件统一编码后，根据目标设备类型路由到相应的底层控制协议。

## API 路由

VmControl 对外暴露 50+ 条 API 路由（独立二进制模式下通过 HTTP 访问）：

| 路由前缀 | 说明 |
|----------|------|
| `/webrtc` | WebRTC 信令（Offer/Answer/ICE） |
| `/device` | 设备连接管理和状态查询 |
| `/command` | 设备命令下发 |
| `/screen` | 屏幕截图和视频流控制 |
| `/scrcpy` | Scrcpy 连接管理 |
| `/bridge` | Cloud Bridge 连接状态和管理 |
| `/input` | 输入事件注入 |
| `/health` | 健康检查 |

## 依赖关系

```
VmControl
├── Device Service      — Cloud Bridge WebSocket 连接（/internal/pc/ws）
├── WebRTC 协议栈       — webrtc-rs crate，UDPMux + Trickle ICE
├── Scrcpy Server       — Android 设备端 scrcpy-server 3.3.4
├── Tauri（嵌入式模式） — 宿主桌面应用框架
└── axum（独立模式）    — HTTP 服务框架
```

VmControl 是设备交互的最底层组件，通过 Cloud Bridge 与 Device 服务协作，通过 WebRTC 向前端提供视频流。
