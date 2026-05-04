# 配置与环境变量

## 后端配置 SSOT

后端服务配置的唯一入口是 `novaic-common/config/services.json`，Python 服务通过 `common.strict_config.load_services_config()` 读取。`scripts/start.sh` 也必须通过同一个 loader 读取配置，不允许在 shell 里手写第二份 overlay merge 逻辑。

`runtime_switches` 的 overlay 顺序由 `common.strict_config` 统一管理：

1. `NOVAIC_RUNTIME_SWITCHES_PATH`：测试 / 临时运维钩子，文件不存在会 fail-fast。
2. `services.json` 同目录的 `runtime_switches.json`：本地开发覆盖。
3. `/opt/novaic/etc/runtime_switches.json`：生产 canonical overlay，位于 rsync 服务目录之外，部署不会覆盖。

允许使用的环境变量只保留三类：OS 标准变量、服务身份变量、测试/CI 专用变量。生产 secrets 和 runtime switches 不再走旧的 env 文件路径。

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

## Cortex 服务（`:19996`）

Cortex 的 JWT、internal key、Blob Service URL 等生产值来自 `services.json`，启动时由 `scripts/start.sh` 作为 CLI 参数显式传入 `main_cortex`。OSS/S3 物理后端配置属于 Blob Service，不属于 Cortex。Agent Runtime 访问 Cortex 的 URL/timeout 也来自 `ServiceConfig`，由同一份 `services.json` 派生。Cortex 不再接收 Business URL，也不提供 BusinessProxy。

---

## 相关

- [../cortex/deployment-and-startup.md](../cortex/deployment-and-startup.md)  
