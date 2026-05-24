# 全服务 API 路由表

## Gateway (:19999)

| 路径 | 方法 | 说明 |
|------|------|------|
| `/api/health` | GET | 健康检查 |
| `/auth/login` | POST | 登录 |
| `/auth/register` | POST | 注册 |
| `/auth/refresh` | POST | 刷新 token |
| `/auth/logout` | POST | 登出 |
| `/auth/oauth/callback` | GET | OAuth 回调 |
| `/ws/signaling` | WS | WebSocket 信令（WebRTC SDP/ICE） |
| `/api/app/ws` | WS | AppBridge WebSocket（push 事件、信令转发） |
| `/api/blobs/upload-config` | POST | Blob 上传配置 |
| `/api/blobs/register` | POST | 注册已上传 Blob |
| `/blob/v1/blobs/{ns}/{id}` | GET | Blob 文件下载代理 |
| `/api/config/frontend` | GET | 前端 OTA 地址发现 |
| `/api/*` | * | 代理到 Business/Cortex 等后端服务 |

## Business (:19998)

| 路径 | 方法 | 说明 |
|------|------|------|
| `/api/users/*` | CRUD | 用户管理 |
| `/api/agents/*` | CRUD | Agent 管理 |
| `/api/devices/*` | CRUD | 设备管理 |
| `/api/skills/*` | CRUD | 技能管理 |
| `/api/models/*` | CRUD | 模型管理 |
| `/api/api-keys/*` | CRUD | API Key 管理 |
| `/api/messages/*` | CRUD | 消息管理 |
| `/api/agent-bindings/*` | CRUD | Agent-Device 绑定 |
| `/api/agent-tools/*` | CRUD | Agent 工具配置 |
| `/api/available-models/*` | CRUD | 可用模型管理 |
| `/api/api-key-models/*` | CRUD | API Key-Model 关联 |
| `/api/vm-users/*` | CRUD | VM 用户管理 |
| `/api/user-preferences/*` | CRUD | 用户偏好 |
| `/api/agent-activity-records/*` | CRUD | Agent 活动记录 |
| `/api/agent-activity-participants/*` | CRUD | Agent 活动参与者 |
| `/internal/*` | * | 内部服务间 API |

> Business 共 9 个 Internal API router，60+ HTTP 路由。19 个 Entity Schema，30+ Action Hooks。

## Queue Service (:19997)

| 路径 | 方法 | 说明 |
|------|------|------|
| `/api/tasks/*` | CRUD | 任务管理 |
| `/api/sagas/*` | CRUD | Saga 管理 |
| `/api/workers/*` | CRUD | Worker 注册与状态 |
| `/api/schedules/*` | CRUD | 调度管理 |
| `/api/health` | GET | 健康检查 |

> Queue Service 共 45+ HTTP 路由，SQLite 持久化。

## Cortex (:19996)

| 路径 | 方法 | 说明 |
|------|------|------|
| `/api/scopes/*` | CRUD | Scope 管理（Redis 分布式锁） |
| `/api/contexts/*` | CRUD | Context 管理 |
| `/api/events/*` | CRUD | ContextEvent 管理（10 种事件类型） |
| `/api/shells/*` | CRUD | Shell 会话管理 |
| `/api/sandboxes/*` | CRUD | Sandbox 管理 |
| `/api/payloads/*` | CRUD | Payload 管理 |
| `/api/health` | GET | 健康检查 |

> Cortex 共 40+ HTTP 路由。

## Device (:19993)

| 路径 | 方法 | 说明 |
|------|------|------|
| `/api/devices/*` | CRUD | 设备管理 |
| `/api/tools/*` | CRUD | Mounted Tools 管理 |
| `/internal/pc/ws` | WS | VmControl Cloud Bridge（typed command 协议） |
| `/api/health` | GET | 健康检查 |

> Device 共 50+ HTTP 路由，支持 3 种设备类型。

## Blob Service (:19995)

| 路径 | 方法 | 说明 |
|------|------|------|
| `/v1/blobs/{namespace}/{blob_id}` | GET/PUT | Blob 原始存储 |
| `/v1/blobs/{namespace}/{blob_id}/upload` | POST | Multipart 分块上传 |
| `/v1/objects/{path}` | GET/PUT/DELETE | Object Tree 结构化操作 |
| `/v1/objects/{path}/children` | GET | 列出子对象 |
| `/api/health` | GET | 健康检查 |

## Sandbox Service (:19994)

| 路径 | 方法 | 说明 |
|------|------|------|
| `/api/execute` | POST | 执行命令（AsyncProcessRunner） |
| `/api/files/*` | CRUD | 文件操作 |
| `/api/health` | GET | 健康检查 |

## LLM Factory (:19990)

| 路径 | 方法 | 说明 |
|------|------|------|
| `/v1/chat/completions` | POST | LLM 推理（Provider 路由） |
| `/v1/config/models` | GET/POST | 模型配置 |
| `/v1/config/api-keys/*` | CRUD | API Key 管理（RSA-2048 加密） |
| `/health` | GET | 健康检查 |

## Service Registry (:19991)

| 路径 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/ready` | GET | 就绪检查 |
| `/v1/registry/namespaces/{namespace}/instances` | POST | 注册或更新同 namespace 服务实例 |
| `/v1/registry/namespaces/{namespace}/instances/{service_name}/{instance_id}/heartbeat` | POST | 同 namespace 实例心跳与状态更新 |
| `/v1/registry/namespaces/{namespace}/instances/{service_name}/{instance_id}` | DELETE | 注销同 namespace 实例 |
| `/v1/registry/namespaces/{namespace}/services/{service_name}/instances` | GET | 列出同 namespace 实例，可按 fresh/discoverable 过滤 |
| `/v1/registry/namespaces/{namespace}/services/{service_name}/discover` | GET | 返回同 namespace 最新 fresh healthy 实例 |
| `/v1/registry/namespaces/{namespace}/services/{service_name}/prune-stale` | POST | 清理同 namespace 过期实例 |

## Entangled (:19900)

| 路径 | 方法 | 说明 |
|------|------|------|
| `/v1/sync` | WS | 实体同步 WebSocket |
| `/api/health` | GET | 健康检查 |

## VmControl (嵌入式 / :19992 独立模式)

| 路径 | 方法 | 说明 |
|------|------|------|
| `/api/vms` | GET | VM 列表 |
| `/api/vms/:id/start\|stop\|pause\|resume` | POST | VM 生命周期 |
| `/api/vms/:id/screenshot` | POST | 截图 |
| `/api/vms/:id/input/keyboard\|mouse` | POST | 输入注入 |
| `/api/vms/:id/guest/exec` | POST | Guest Agent 命令 |
| `/api/vms/:id/users` | GET/POST | VM 用户管理 |
| `/api/vms/:id/vmuse/:tool/:operation` | POST | VMUSE 代理 |
| `/api/vms/:id/browser/*` | POST | 浏览器控制 |
| `/api/webrtc/start\|stop` | POST | WebRTC 管理 |
| `/api/android/*` | * | Android 设备/AVD 管理 |
| `/api/hd/:tool/:operation` | POST | Host Desktop 工具代理 |
| `/health` | GET | 健康检查 |

> VmControl 共 50+ API 路由。
