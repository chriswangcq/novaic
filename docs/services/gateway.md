# Gateway API 网关

## 概述与职责

Gateway 是 Novaic 平台的 API 网关服务，运行在端口 `:19999`，基于 Python / FastAPI 构建。它是所有外部客户端请求的统一入口，负责认证鉴权、请求路由、WebSocket 信令和协议转换。

核心职责包括：

- 统一的外部 API 入口，隔离内部服务拓扑
- 双 JWT 认证体系，区分外部用户和内部服务
- WebSocket 信令服务，支撑前端实时通信
- Blob 代理路由，统一文件访问入口
- OAuth 回调处理，集成第三方身份提供商

## 认证体系（双 JWT）

Gateway 实现了两套独立的 JWT 认证方案，分别服务于不同的调用场景：

### Clerk RS256（外部认证）

| 属性 | 说明 |
|------|------|
| 签名算法 | RS256（非对称） |
| 密钥来源 | Clerk JWKS 端点动态获取公钥 |
| 适用场景 | 外部客户端（Web App、Mobile App） |
| Token 来源 | Clerk 身份服务签发 |
| 验证流程 | 获取 JWKS → 匹配 kid → RS256 验证签名 → 校验 claims |

### Internal HS256（内部认证）

| 属性 | 说明 |
|------|------|
| 签名算法 | HS256（对称） |
| 密钥来源 | 服务间共享密钥（环境变量配置） |
| 适用场景 | 服务间内部调用 |
| Token 来源 | 各内部服务自行签发 |
| 验证流程 | 使用共享密钥 HS256 验证签名 → 校验 claims |

请求处理时，Gateway 先尝试 Clerk RS256 验证，失败后回退到 Internal HS256。两种方式都失败则返回 401。

```
外部请求（Bearer Token）
    ↓
尝试 Clerk RS256 验证
    ├── 成功 → 提取用户身份，继续处理
    └── 失败 ↓
        尝试 Internal HS256 验证
            ├── 成功 → 标记为内部调用，继续处理
            └── 失败 → 返回 401 Unauthorized
```

## 路由结构

Gateway 的路由通过 `routers/` 目录下的模块组织，每个模块负责一个功能域：

| 路由模块 | 路径前缀 | 说明 |
|----------|----------|------|
| Agent | `/api/agent` | Agent 操作（启动、停止、对话） |
| Session | `/api/session` | 会话管理和消息收发 |
| Device | `/api/device` | 设备查询和操作 |
| User | `/api/user` | 用户信息和偏好设置 |
| Model | `/api/model` | 模型列表和配置 |
| File | `/api/file` | 文件上传和下载 |
| Blob | `/api/blob` | Blob 存储代理 |
| OAuth | `/api/oauth` | OAuth 回调和授权 |
| Health | `/health` | 健康检查 |

Gateway 将 `/api/*` 请求在鉴权后转发到对应的内部服务，本身不包含业务逻辑。

## WebSocket 信令

Gateway 在 `/ws/signaling` 路径上提供 WebSocket 信令服务，用于前端和后端之间的实时通信：

- **连接建立**：客户端通过 WebSocket 连接到 `/ws/signaling`，携带认证 Token。
- **信令类型**：支持 WebRTC 信令交换（Offer/Answer/ICE Candidate）、设备状态通知、Agent 执行状态推送。
- **连接管理**：维护连接池，支持按用户/会话维度的消息路由。
- **心跳机制**：定期 Ping/Pong 检测连接存活，超时自动清理。

信令服务是前端实时体验的基础，特别是 WebRTC 视频流连接的建立依赖于此信令通道。

## Blob 代理

Gateway 提供 Blob 代理路由，将文件访问请求统一代理到 Blob Service：

- **上传代理**：客户端通过 Gateway 上传文件，Gateway 转发到 Blob Service 并返回 blob:// URI。
- **下载代理**：客户端通过 Gateway 请求 blob:// URI 对应的文件，Gateway 从 Blob Service 获取并返回。
- **访问控制**：Gateway 在代理过程中进行权限校验，确保用户只能访问自己有权的文件。

这种设计避免了客户端直接访问 Blob Service，保持了内部服务的网络隔离。

## 依赖关系

```
Gateway
├── Clerk         — 外部 JWT 验证（JWKS 公钥获取）
├── Business      — 业务实体 API 代理转发
├── Agent Runtime — Agent 操作请求转发
├── Blob Service  — 文件上传/下载代理
├── Device        — 设备操作请求转发
└── Cortex        — 上下文相关请求转发
```

Gateway 作为唯一的外部入口，与几乎所有内部服务存在调用关系，但它本身是无状态的纯代理层。
