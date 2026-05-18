# Device 设备管理

## 概述与职责

Device 是 Novaic 平台的设备管理服务，运行在端口 `:19993`，基于 Python / FastAPI 构建。它负责管理平台中所有受控设备的注册、状态跟踪、命令下发和工具挂载，是 Agent 与物理/虚拟设备交互的桥梁。

核心职责包括：

- 管理多种设备类型的注册和生命周期
- 提供类型化命令的 WebSocket 通信协议
- 实现 Mounted Tools 系统，将工具能力绑定到设备
- 与 VmControl / CloudBridge 集成，实现云端设备控制

## 类型化命令 WebSocket 协议

Device 服务在 `/internal/pc/ws` 路径上提供 WebSocket 端点，用于与 VmControl（Cloud Bridge）之间的双向类型化命令通信：

### 协议设计

```
Device Service                    VmControl / Cloud Bridge
     │                                      │
     │◄──── WebSocket 连接建立 ──────────────│
     │                                      │
     │──── 类型化命令（JSON） ──────────────►│
     │                                      │
     │◄──── 命令结果（JSON） ───────────────│
     │                                      │
     │◄──── 状态上报（JSON） ───────────────│
```

### 命令结构

每条命令是一个类型化的 JSON 消息，包含：

| 字段 | 类型 | 说明 |
|------|------|------|
| `command_type` | string | 命令类型标识 |
| `command_id` | string | 唯一命令 ID，用于匹配响应 |
| `device_id` | string | 目标设备 ID |
| `payload` | object | 命令参数载荷 |
| `timeout` | int | 命令超时时间（毫秒） |

Cloud Bridge 定义了约 30 种类型化命令，涵盖鼠标操作、键盘输入、屏幕截图、文件传输、进程管理等。

## 设备类型

系统支持 3 种设备类型，每种有不同的通信方式和能力集：

| 设备类型 | 说明 | 通信方式 | 典型场景 |
|----------|------|----------|----------|
| `linux` | Linux 虚拟机 | WebSocket 命令 + WebRTC 视频 | 云端 Agent 工作环境 |
| `android` | Android 设备 | Scrcpy 协议 + WebSocket 命令 | 移动端自动化 |
| `host_desktop` | 宿主桌面 | 本地进程通信 | 本地开发和调试 |

每种设备类型在注册时会声明其支持的能力列表（如 `screen_capture`、`keyboard_input`、`file_transfer` 等），Agent Runtime 根据能力选择合适的操作方式。

## Mounted Tools 系统

Mounted Tools 是 Device 服务的工具挂载机制，允许将特定工具能力动态绑定到设备实例：

### 工作原理

1. **工具定义**：在系统中注册工具的元数据（名称、参数 Schema、执行方式）。
2. **工具挂载**：将工具绑定到特定设备，建立设备-工具关联。
3. **工具发现**：Agent Runtime 查询设备的已挂载工具列表，供 Agent 推理时使用。
4. **工具执行**：Agent 选择工具后，通过 Device 服务的 WebSocket 通道下发到设备执行。

### 设计优势

- **动态绑定**：工具可在运行时挂载/卸载，无需重启服务。
- **设备感知**：同一工具在不同设备类型上可有不同实现。
- **能力协商**：只暴露设备实际支持的工具，避免无效调用。

## API 路由

Device 服务对外暴露 50+ 条 HTTP API 路由：

| 路由前缀 | 说明 |
|----------|------|
| `/internal/device` | 设备注册、查询、状态更新、删除 |
| `/internal/device/{id}/command` | 向设备发送命令 |
| `/internal/device/{id}/tools` | 设备已挂载工具查询和管理 |
| `/internal/device/{id}/screen` | 屏幕截图和视频流管理 |
| `/internal/pc/ws` | WebSocket 命令通道 |
| `/internal/pool` | 设备池管理（创建、查询、分配） |
| `/internal/mount` | 工具挂载和卸载操作 |
| `/health` | 健康检查 |

## 依赖关系

```
Device
├── VmControl / Cloud Bridge — 通过 WebSocket 下发设备命令
├── Business                 — 设备实体和配置数据
└── Redis                    — 设备在线状态缓存和命令队列
```

Device 服务被 Agent Runtime 频繁调用，是 Agent 执行设备操作的唯一通道。
