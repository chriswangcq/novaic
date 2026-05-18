# Gateway 内部接口与 Worker 边界

> 当前 Gateway 只保留内部 auth 和 App push/signaling 边界。Runtime Worker 的产品 API 不再通过 Gateway。

## 1. Gateway 仍保留的内部接口

- `GET /internal/auth/validate`：供 Nginx `auth_request` 或内部校验使用。
- `POST /api/app/push`：Business 将用户定向 push 送回 App WS。
- WebRTC signaling 相关 App WS handler：App 侧 offer/ICE 进入 Gateway，再转发到 Business signaling API。

## 2. Worker 当前调用对象

Runtime Worker 的主协作者是：

- **Queue Service**：Task/Saga/session 调度；
- **Business**：Environment IM、SubAgent、产品配置、设备编排；
- **Cortex**：scope/context/tool observation；
- **LLM Factory**：模型 provider 调用。

Gateway 不再提供 handler execution、business entry、entity CRUD 或 Runtime context 组装接口。

## 3. 信令返回路径

```text
Device / VmControl event
  → Business /internal/signaling
  → Gateway /api/app/push
  → App WS
```

这条路径只用于用户在线连接的 push/signaling，不是业务状态写入通道。

