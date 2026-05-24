# REST 路由与验证流转：Auth & Deps

> 路径参考：`novaic-gateway/gateway/api/auth.py` 和 `gateway/infra/deps.py`

## 1. 路由模块化组织
Gateway 的对外 REST 端点以极其清爽的 FastAPI router 结构包裹，但当前不再承载产品实体 CRUD 或设备/VM 编排。保留在 Gateway 的 HTTP 面主要是边缘能力：
- `/auth/login` 等认证分发
- `/api/turn/credentials` 对 WebRTC P2P 的票据供应
- Blob edge 与 App WS/signaling 相关入口

产品实体写入走 App → Entangled action/sync → Business action hook；设备和 VM 行为由 Business 编排到 Device Service 执行。

## 2. 身份流转逻辑：Token VS. 边界网关
由于需要承接来自桌面应用程序以及公开网页版两种完全不同且有可能极不安全的访问，身份认定被设定为**严格的双轨防御验证**：

1. **桌面端的直接访问 (Bearer Token)**:
   客户端把持着由 Gateway `/auth/login` 签发的 HS256 JWT Token。这些 Token 内包裹好了 `sub` 声明的身份标志。通过 HTTP `Authorization: Bearer` 发向后端。

2. **Nginx 介入（`auth_request`）与防伪冒**:
   所有的 Web HTTP 请求到达时，常常要在挂在边缘 Nginx 内经过 `/internal/auth/validate` 这一接口鉴权；鉴权成功时，Nginx 在内部透传请求内埋入 Header `X-User-ID`。
   在代码依赖链 `deps.py -> get_current_user()` 函数里，**第一优先且致命的验证其实是 JWT Token**：即使内部携带了 Header，但如果里面解签发现 `sub` 跟被声明的 `X-User-ID` 不一致对不上号，则强制认定发生了伪造并予以 403 阻断处理（即“绝不盲从内部头，必须交叉验证”）。
   除非环境变量中设置了特殊的 `TRUST_GATEWAY_X_USER_ID=true` 用作纯前端隔离层，才会把 Header 当做主来源。

## 3. 全局依赖切面
基于 FastAPI 强劲的 Dependency Injection，路由无需关注脏活累活。每个具有用户态的方法仅需：
`def send_message(current_user = Depends(get_current_user))`
一旦验证走过此处，整个网关的 Repository 的一切获取在 SQL 条件中自动包裹带上了属于本人的 `WHERE user_id = ?`，全方位保证了租户信息隔离。
