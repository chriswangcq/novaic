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
| `TRUST_GATEWAY_X_USER_ID` | 默认 `true`：无 Bearer 时可信任 nginx 注入的 `X-User-ID`。公网直连防伪造时可为 `false`。 |
| `INTERNAL_TASKS_SECRET` | 非空时：`/api/internal/tasks*` 须带 `X-Internal-Secret`；跨主机需配置。 |
| `DEV_MODE` | 未授权时的调试日志，不改变生产主逻辑。 |

更多本地路径见 [../reference/config-and-environment.md](../reference/config-and-environment.md)。
