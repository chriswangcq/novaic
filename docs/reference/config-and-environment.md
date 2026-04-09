# 配置与环境变量

> 对应 **`HANDOVER.md` §十四、§8.5**。生产值以服务器实际配置为准。

## 本地 App 数据目录（macOS）

`~/Library/Application Support/com.novaic.app`

可含：`gateway_url.txt`、`api_key.txt`、`app.pid`；日志等见 `logs/`。

**VmControl**（摘要）：

- QMP：`/tmp/novaic/novaic-qmp-{agent_id}.sock`
- VNC：`/tmp/novaic/novaic-vnc-{id}.sock`

## 前端 `config/index.ts`（摘要）

| 区域 | 内容 |
|------|------|
| API_CONFIG | `GATEWAY_URL`、`HTTP_TIMEOUT` |
| LAYOUT_CONFIG | 断点、抽屉宽度等 |
| POLL_CONFIG | `GATEWAY_HEALTH_INTERVAL` 等 |

## Gateway 进程（鉴权 / 内部任务）

与 **`gateway/infra/deps.py`** 对齐：

- `TRUST_GATEWAY_X_USER_ID`、`INTERNAL_TASKS_SECRET`、`DEV_MODE` — 见 [../architecture/authentication.md](../architecture/authentication.md)。
- 跨 Docker/主机调用 **`/api/internal/tasks*`** 时须配置 **`INTERNAL_TASKS_SECRET`** 并带 `X-Internal-Secret`。

**本地单测（无 pytest 依赖 unittest）**：

```bash
cd novaic-gateway && PYTHONPATH=. python -m unittest tests.test_deps_internal_tasks -v
```

## 生产环境变量文件

生产常见： **`/opt/novaic/jwt_secret.env`**（`JWT_SECRET`、`TURN_SECRET`、`FRONTEND_CDN_URL` 等），由 systemd 或部署脚本加载。

---

## Cortex 服务（`:19996`）

与 **`novaic-cortex`** 子模块 **`main_cortex.py`** / **`api.py`** 对齐；详细表见 **[../cortex/deployment-and-startup.md](../cortex/deployment-and-startup.md)**。

| 变量 | 用途 |
|------|------|
| **`CORTEX_HOST`** / **`CORTEX_PORT`** | 监听地址（默认 `0.0.0.0:19996`） |
| **`ALIBABA_CLOUD_ACCESS_KEY_ID`** / **`ALIBABA_CLOUD_ACCESS_KEY_SECRET`** | OSS 必填 |
| **`NOVAIC_OSS_ENDPOINT`** / **`NOVAIC_OSS_REGION`** / **`NOVAIC_OSS_BUCKET`** | OSS 端点与桶 |
| **`CORTEX_JWT_SECRET`** | 能力 JWT 签名（`auth.py`） |
| **`GATEWAY_INTERNAL_URL`** | Gateway 基址（`GatewayProxy`） |
| **`CORTEX_INTERNAL_KEY`** | `X-Internal-Key`（与 Gateway 互信） |

**Agent Runtime**（`CortexBridge`）：

| 变量 | 默认 | 说明 |
|------|------|------|
| **`NOVAIC_CORTEX_URL`** | `http://127.0.0.1:19996` | Cortex HTTP 基址 |
| **`NOVAIC_CORTEX_ENABLED`** | `true` | `false` 关闭桥接 |
| **`NOVAIC_CORTEX_TIMEOUT`** | `30` | 秒 |

---

## 相关

- [../cortex/deployment-and-startup.md](../cortex/deployment-and-startup.md)  
- [../cortex/proxy-cli-auth.md](../cortex/proxy-cli-auth.md)  
