# novaic-app 桌面/移动客户端

## 概述与技术栈

novaic-app 是平台的跨端客户端应用，采用 **Tauri 2.x (Rust) + React 18 + TypeScript** 技术栈，同时支持桌面端和移动端。

| 层级 | 技术 | 职责 |
|-----|------|------|
| 原生壳 | Tauri 2.x (Rust) | 窗口管理、系统调用、安全存储、网络代理 |
| 视图层 | React 18 + TypeScript | UI 渲染、组件交互、状态管理 |
| 状态 | Zustand + TanStack Query | 全局状态、服务端缓存 |
| 同步 | Entangled Client (Rust) | 实体数据实时同步 |
| 国际化 | i18n | 支持 12 种语言 |

**核心设计特点：**

- **前端零直连** — 所有 HTTP/WS 请求都通过 Tauri IPC 转发，前端不直接连接后端
- **悲观优先 + 乐观展示** — 数据写入以服务端确认为准，但 UI 乐观更新以提升体验
- **15 个同步实体** — users、agents、devices、skills、messages 等通过 Entangled 协议实时同步

## React 组件结构

组件按功能领域组织，`src/components/` 下包含 **13 个子目录**：

```
src/components/
├── Agent/          # Agent 管理与配置
├── Auth/           # 登录、注册、认证
├── Chat/           # 聊天面板与消息渲染
├── Console/        # 控制台/开发者工具
├── Layout/         # 布局容器与导航
├── Settings/       # 设置页面
├── VM/             # 虚拟机管理与显示
├── Visual/         # 可视化组件
├── Device/         # 设备管理
├── Skill/          # 技能管理
├── Model/          # 模型配置
├── Common/         # 通用/共享组件
└── ...             # 其他功能模块
```

**组件树概览：**

```
App
 ├── AuthPage                    （未认证时）
 │
 └── LayoutContainer             （已认证时）
      ├── PrimaryNav             左侧主导航栏
      ├── AgentDrawer            Agent 抽屉面板
      └── [Main Content]         主内容区
           ├── ChatPanel         聊天面板
           ├── DeviceManagerPage 设备管理
           ├── SettingsPage      设置页面
           ├── VMPanel           虚拟机面板
           └── ...               其他页面
```

**响应式布局：**

| 端 | 布局结构 | 说明 |
|---|---------|------|
| 桌面端 | 三栏布局 | PrimaryNav（左） + AgentDrawer（中） + Main（右） |
| 移动端 | 单栏布局 | 主内容区 + BottomTabBar（底部标签栏） |

## Tauri 命令体系

应用注册了 **27 个 Tauri 命令**，这些命令通过 Rust 实现并暴露给前端 JavaScript 调用，涵盖以下类别：

| 类别 | 命令数 | 说明 |
|-----|-------|------|
| Gateway 代理 | ~8 | 代理转发前端 HTTP 请求到 Gateway |
| 安全存储 | ~4 | Token/凭证的加密存储与读取 |
| 文件缓存 | ~3 | 本地文件缓存管理 |
| 音频录制 | ~3 | 麦克风录音、编码、停止 |
| WebRTC 信令 | ~4 | SDP 交换、ICE 候选、连接管理 |
| Entangled 同步 | ~3 | 同步连接建立、实体订阅、状态查询 |
| 系统 | ~2 | 平台检测、窗口控制 |

**调用方式：** 前端通过 `@tauri-apps/api` 的 `invoke` 函数调用这些命令：

```typescript
// 示例：通过 Tauri 命令代理 HTTP 请求
const response = await invoke('gateway_request', {
  method: 'GET',
  path: '/api/agents',
  headers: { Authorization: `Bearer ${token}` }
});
```

## 状态管理

应用采用 **Zustand + TanStack Query** 的双轨状态管理方案：

### Zustand（客户端状态）

| Store | 职责 |
|-------|------|
| 主 Store | 全局 UI 状态、当前用户、当前 Agent、布局模式 |
| Device Status Store | 设备在线状态、连接信息 |

### TanStack Query（服务端缓存）

| 配置项 | 值 | 说明 |
|-------|-----|------|
| staleTime | Infinity | 数据永不自动过期 |
| 刷新策略 | 事件驱动 | 仅在收到变更事件时重新获取 |

```
                  ┌───────────────┐
                  │  TanStack     │
  Entangled ────► │  Query Cache  │ ◄──── 事件驱动 invalidation
  事件通知        │  staleTime=∞  │
                  └───────┬───────┘
                          │
                  ┌───────▼───────┐
                  │   React 组件  │
                  │   useQuery()  │
                  └───────────────┘
```

**设计要点：** `staleTime=Infinity` 意味着 TanStack Query 不会自动轮询刷新数据。数据更新完全依赖 Entangled 同步事件触发 `queryClient.invalidateQueries()`，实现精确的按需刷新。

## 路由机制

应用**未使用 react-router**，而是实现了基于布局状态的自定义路由机制。

**核心状态：**

| 状态字段 | 类型 | 说明 |
|---------|------|------|
| primaryTab | enum | 主标签页（Chat / Device / Settings / VM 等） |
| narrowPage | string \| null | 窄屏页面（移动端专用，覆盖主内容区） |

**路由逻辑：**

```
渲染判断:
  if (narrowPage)
    → 渲染 narrowPage 对应组件（移动端全屏覆盖）
  else
    → 根据 primaryTab 渲染对应主面板
```

这种方式避免了 URL 路由的复杂性，适合 Tauri 这类非传统浏览器环境。布局状态存储在 Zustand store 中，切换页面只是修改状态值。

## Entangled 客户端集成

Entangled 客户端由 Rust crate 实现（位于 `Entangled/packages/client-rust/`），通过 WebSocket 与 Entangled 服务保持长连接，实现实体数据的实时同步。

**WebSocket 协议消息类型：**

| 消息类型 | 方向 | 说明 |
|---------|------|------|
| Entangle | 客户端 → 服务端 | 订阅实体/表 |
| Disentangle | 客户端 → 服务端 | 取消订阅 |
| Action | 双向 | 数据变更操作（增/删/改） |
| Sync | 服务端 → 客户端 | 全量/增量数据同步 |
| Ack | 服务端 → 客户端 | 操作确认 |
| Schema | 服务端 → 客户端 | 表结构定义 |

**本地持久化：** 客户端使用 **SQLite** 作为本地缓存，确保离线状态下仍可读取最近同步的数据。重新上线后自动增量同步。

**同步的 15 类实体：** users、agents、devices、skills、messages、conversations、models、vm_instances、files、settings、permissions、teams、notifications、audit_logs、schedules 等。

## 前后端通信架构

应用维护 **3 个通信通道**，所有通道都经由 Tauri Rust 层代理：

```
┌─────────────────────────────────────────────────────┐
│                   React 前端                         │
│                                                      │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ Gateway  │  │  AppBridge   │  │  Entangled    │  │
│  │ Client   │  │  WS Client   │  │  SyncBridge   │  │
│  └────┬─────┘  └──────┬───────┘  └───────┬───────┘  │
│       │               │                  │           │
└───────┼───────────────┼──────────────────┼───────────┘
        │  Tauri IPC    │  Tauri IPC       │  Tauri IPC
┌───────▼───────────────▼──────────────────▼───────────┐
│                  Tauri Rust 层                        │
│                                                      │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  HTTP    │  │  WebSocket   │  │  WebSocket    │  │
│  │  Proxy   │  │  Proxy       │  │  Proxy        │  │
│  └────┬─────┘  └──────┬───────┘  └───────┬───────┘  │
└───────┼───────────────┼──────────────────┼───────────┘
        │               │                  │
        ▼               ▼                  ▼
     Gateway         Gateway            Entangled
     (REST)        (信令+推送)          (实体同步)
```

**三大通道详解：**

| 通道 | 协议 | 职责 |
|-----|------|------|
| GatewayClient | HTTP (REST) | 常规 API 请求（CRUD 操作） |
| AppBridge | WebSocket | 信令交换（WebRTC）、服务端推送通知 |
| EntangledSyncBridge | WebSocket | 实体数据实时双向同步 |

**Tauri 事件系统（6 个事件）：**

| 事件名 | 触发时机 | 消费方 |
|-------|---------|--------|
| entities_changed | Entangled 实体变更 | TanStack Query invalidation |
| schema_changed | 表结构变更 | 本地 Schema 更新 |
| auth_rejected | 认证失效 | 跳转登录页 |
| gateway_push | 服务端推送 | UI 通知/状态更新 |
| bridge_connected | WS 连接建立 | 连接状态指示器 |
| bridge_disconnected | WS 连接断开 | 重连逻辑/离线提示 |

**服务层单例：** 按 `userId` 维度创建服务单例，确保同一用户的服务实例全局唯一：

- SyncService — 实体同步管理
- AgentService — Agent 操作封装
- ModelService — 模型配置与调用
- LayoutService — 布局状态管理
- DeviceService — 设备管理
- VmUserService — VM 用户操作
- SkillsService — 技能管理
- ModelConfigService — 模型配置管理
