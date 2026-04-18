# 认证体系（JWT）

> 对应 **`HANDOVER.md` §8**。Gateway 实现以 `novaic-gateway` 源码为准。

## 流程（概要）

```
用户 → POST /auth/login → Gateway 返回 HS256 JWT + refresh_token
     → 前端 localStorage → App.tsx update_cloud_token → Rust 请求带 Authorization: Bearer
     → Nginx auth_request → /internal/auth/validate → X-User-ID
     → Gateway Depends(get_current_user) → 业务按 user_id 过滤
```

## Token 参数

| 项 | 典型值 |
|----|--------|
| 算法 | HS256 |
| Access TTL | 60 分钟 |
| Refresh TTL | 30 天（轮换） |
| 前端刷新 | 距过期 &lt; 5 分钟自动 `/auth/refresh`；约每 55 分钟推送 Rust |
| 密钥 | 生产 `JWT_SECRET` 在 `/opt/novaic/jwt_secret.env` |

## 多租户隔离

- 业务表带 `user_id`，Repository 查询强制过滤。
- SSH Key 路径：`{DATA_DIR}/.ssh/id_rsa_{user_hash}`（sha256 前 16 位）。
- 客户端伪造的 `X-User-ID` 在 Nginx 层剥离。

## 关键文件（子模块内）

| 路径 | 作用 |
|------|------|
| `novaic-app/src/services/auth.ts` | login / refresh / getAccessToken |
| `novaic-app/src/App.tsx` | AuthScreen、pushToken |
| `novaic-app/src-tauri/src/setup.rs` | Gateway URL 等注入 |
| `novaic-app/src-tauri/vmcontrol/.../cloud_bridge.rs` | CloudBridge WS 握手读 token |
| `novaic-gateway/gateway/api/auth.py` | login / refresh / validate |
| `novaic-gateway/gateway/infra/deps.py` | `get_current_user`、`verify_internal_tasks` |
| `novaic-gateway/gateway/nginx/novaic-cloud.conf` | auth_request |

## 环境变量（与 `deps.py` 一致）

| 变量 | 含义 |
|------|------|
| `TRUST_GATEWAY_X_USER_ID` | 默认 `true`（仅在 Gateway 绑 `127.0.0.1` + 可信 nginx `auth_request` 注入 `X-User-ID` 的部署模式下安全）。**P3-4 生产硬化**：公网直连 / 容器网络等任何"非 loopback"暴露都应显式 `false`，强制 Bearer JWT 鉴权。Gateway 启动时会检测绑定地址并 `WARN` 非法组合（见 `main_gateway.py::lifespan`）。 |
| `INTERNAL_TASKS_SECRET` | 非空时：`/api/internal/tasks*` 须带 `X-Internal-Secret`；跨主机需配置。 |
| `DEV_MODE` | 未授权时的调试日志，不改变生产主逻辑。 |

更多本地路径见 [../reference/config-and-environment.md](../reference/config-and-environment.md)。

## 内部调用的 caller 归因

从 **PR-06** 开始，所有内部服务调用必须通过 HTTP Header `X-Internal-Service` 传递调用方的服务名。
- **解析中间件**：`novaic-common/common/middlewares/caller_logging.py` 会在各服务 `main_*.py` 中注册。
- **日志格式**：自动生成 `caller=<service_name>` 字段及 `internal=1` 到访问日志，保证 ELK 等系统可准确追踪内网来源。
- **ContextVar 传递**：利用 `common.log_context.caller_var` 在同一进程的不同异步协程间透传 caller（为将来的 LogContext 做准备）。
- **校验逻辑**：灰度期间对于缺失 caller 的请求只打 WARN 级日志而不触发 401。

## 内部所有权解析 (AgentOwnershipResolver)

从 **PR-08** 开始，系统不再依赖上游接口透传或拼装 `user_id`，而是通过内部 HTTP 请求统一通过 Business 获取。
- **所有权隔离**：业务端查询 404（无论是不存在还是无主），都会被统一收敛抛出 `AgentNotOwnedError`，以对调用方屏蔽底层存储差异。
- **Cortex 租户约束止于 Assembler**：Cortex 的强 tenant 约束（`user_id`, `agent_id`）从架构上将止步于 `DispatchAssembler` 层。后续调度与执行将基于 Assembler 的信任体系与内部身份传递，不再外泄该鉴权要求至更上游的网络契约中。
