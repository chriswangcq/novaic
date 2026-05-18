# 认证与身份体系

本文档描述 Novaic 平台的认证架构，包括外部用户认证（Clerk RS256 JWT）、内部服务间认证（HS256 JWT）、客户端 Token 管理以及各通信通道的认证方式。

## 认证架构总览

```
┌─────────────────────────────────────────────────────────────────────┐
│                        认证边界                                      │
│                                                                      │
│  ┌──────────┐    Clerk RS256 JWT    ┌──────────────────────────────┐ │
│  │   App    │──────────────────────►│          Gateway             │ │
│  │  (Tauri) │                       │          :19999              │ │
│  └──────────┘                       │  ┌────────────────────────┐ │ │
│                                     │  │   Auth Middleware       │ │ │
│                                     │  │                        │ │ │
│                                     │  │  RS256 ──► Clerk 公钥  │ │ │
│                                     │  │  HS256 ──► 共享密钥    │ │ │
│                                     │  └────────────────────────┘ │ │
│                                     └──────────┬───────────────────┘ │
│                                                │ HS256 JWT            │
│                           ┌────────────────────┼────────────────┐    │
│                           ▼                    ▼                ▼    │
│                      ┌─────────┐        ┌──────────┐    ┌─────────┐ │
│                      │Business │        │  Cortex  │    │ Device  │ │
│                      │ :19998  │        │  :19996  │    │ :19993  │ │
│                      └─────────┘        └──────────┘    └─────────┘ │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

系统采用双层 JWT 认证机制：

| 层级 | 算法 | 签发方 | 用途 |
|------|------|--------|------|
| 外部认证 | RS256 | Clerk | 用户面客户端请求认证 |
| 内部认证 | HS256 | Gateway / 内部服务 | 服务间通信认证 |

## 外部认证（Clerk RS256）

Clerk 作为外部身份提供商，负责用户注册、登录和 JWT 签发。

### 认证流程

```
用户登录                 Clerk 服务
   │                        │
   │  OAuth/密码/SSO 登录   │
   │───────────────────────►│
   │                        │
   │  RS256 JWT (含 user_id, │
   │  org_id, permissions)  │
   │◄───────────────────────│
   │                        │
   ▼
App 存储 JWT ──► 后续请求携带 Authorization: Bearer <jwt>
```

### JWT Payload 关键字段

| 字段 | 说明 |
|------|------|
| `sub` | 用户唯一标识 (Clerk user ID) |
| `org_id` | 所属组织 ID |
| `azp` | 授权方（Authorized Party） |
| `exp` | 过期时间 |
| `iat` | 签发时间 |
| `permissions` | 权限列表 |

Gateway 使用 Clerk 公钥验证 RS256 签名，校验 `exp` 和 `azp` 字段。

## 内部认证（HS256 JWT）

服务间通信使用 HS256 对称加密 JWT，密钥由配置统一管理。

| 特性 | 说明 |
|------|------|
| 签发方 | Gateway 在转发请求时重新签发 |
| 算法 | HS256（HMAC-SHA256） |
| 密钥 | 部署时注入的共享密钥 |
| 有效期 | 短时效（通常几分钟） |
| Payload | 携带 `user_id`、`org_id`、`device_id` 等业务上下文 |

Gateway 收到外部 RS256 JWT 后：验证签名和有效期 → 提取 user_id/org_id → 签发 HS256 内部 JWT → 附加到转发请求的 Authorization header。内部服务只需验证 HS256 签名即可信任请求身份。

## 客户端 Token 管理

### Token 存储与更新

```
┌─────────────────────────────────────────────────────┐
│                   App (Tauri)                        │
│                                                      │
│  ┌──────────────┐         ┌───────────────────────┐ │
│  │  React 前端   │  IPC    │      Rust 后端         │ │
│  │              │────────►│                        │ │
│  │  Clerk SDK   │ update_ │  ┌──────────────────┐ │ │
│  │  获取 JWT    │ cloud_  │  │ Secure Storage   │ │ │
│  │              │ token   │  │ (RwLock<String>) │ │ │
│  └──────────────┘         │  └──────────────────┘ │ │
│                           └───────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

| 步骤 | 动作 | 说明 |
|------|------|------|
| 1 | React: Clerk SDK 登录 | 获取 RS256 JWT |
| 2 | React: `update_cloud_token` Tauri command | 将 JWT 推送到 Rust 侧 |
| 3 | Rust: 写入 `RwLock<String>` | 安全存储，供各客户端组件读取 |
| 4 | 后续请求自动携带 | HTTP client 和 WS 连接均从 RwLock 读取最新 Token |

### Token 刷新流程

服务端返回 401 或触发 `auth_rejected` 事件时：React 监听事件 → Clerk SDK 刷新 Token → `update_cloud_token` 推送新 JWT 到 Rust → RwLock 更新 → WS 自动重连 / HTTP 自动重试。

## 服务间认证

### 各通道认证方式

| 通道 | 认证方式 | Header / 参数 |
|------|---------|---------------|
| App → Gateway (HTTP) | Clerk RS256 JWT | `Authorization: Bearer <clerk_jwt>` |
| Gateway → 内部服务 (HTTP) | HS256 JWT | `Authorization: Bearer <internal_jwt>` |
| App ↔ Gateway (AppBridge WS) | Clerk RS256 JWT | `Authorization: Bearer <clerk_jwt>` （握手时） |
| App ↔ Entangled (WS) | Clerk RS256 JWT | TauriAuthProvider 从 RwLock 读取 |
| Device ↔ VmControl (Cloud Bridge WS) | JWT + 设备标识 | `Authorization: Bearer <jwt>` + `x-device-id` + `x-app-instance-id` |
| Agent Runtime → 外部服务 (HTTP) | HS256 JWT | 内部签发，携带 task 上下文 |

### Cloud Bridge 特殊认证

Device Service 与 VmControl 之间的 Cloud Bridge WS 连接需要额外的设备标识：

| Header | 说明 |
|--------|------|
| `Authorization` | Bearer JWT |
| `x-device-id` | 设备唯一标识 |
| `x-app-instance-id` | App 实例标识（区分同一设备多开） |

### 认证失败处理

| 场景 | 返回码 | 客户端行为 |
|------|--------|-----------|
| JWT 过期 | 401 Unauthorized | 触发 Token 刷新流程 |
| JWT 签名无效 | 401 Unauthorized | 提示重新登录 |
| 权限不足 | 403 Forbidden | 展示权限不足提示 |
| WS 认证失败 | 连接关闭 + auth_rejected 事件 | 刷新 Token 后自动重连 |
| 内部服务 HS256 校验失败 | 401 | 记录告警日志，拒绝请求 |
