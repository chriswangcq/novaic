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
