# 部署（Runbook）

Release Controller 是后端和 LLM Factory 的唯一发布入口。父仓库根目录 **`deploy`** 仍然存在，但它对 backend/factory image targets 只是 Release Controller 的内部执行器；人工直接调用这些发布入口会失败。

> **原理、Gateway/Relay/Factory 主机表、OTA 三处同步、维护命令** 的完整版见 [**`cloud-production.md`**](cloud-production.md)。本节为命令速查。

细节以仓库内 **`./deploy` 源码**和 Release Controller 状态 API 为准。

## 前置

- 已配置对 **`api.gradievo.com`**、**relay** 等的 SSH（脚本内写死主机别名，见 `deploy` 顶部变量）；LLM Factory 当前也在 API host Docker 上。
- 子模块目录存在且可同步（如 `novaic-gateway`、`novaic-app`）。
- Release Controller 是唯一后端/Factory 发布入口，当前运行在 API host 的 `127.0.0.1:19880`，不走公网 Nginx。
- GitHub Actions 不再承担 backend/factory 构建、发布、promote 或 rollback；branch polling、trigger、promotion、rollback 都由 Release Controller 执行。

## 常用命令

| 目标 | 命令 |
|------|------|
| 前端 OTA | `./deploy frontend [version]`（默认版本见脚本内 `VERSION`） |
| API 后端 / LLM Factory staging | Release Controller polling 或 `POST /v1/triggers` |
| API 后端 / LLM Factory prod | `POST /v1/promotions/prod` |
| API 后端 / LLM Factory rollback | `POST /v1/rollbacks/<namespace>` |
| Release Controller（中心化 CD 控制面） | `./deploy release-controller-image <image-ref>` |
| Host infra（Redis/coturn/QUIC Docker，nginx 保留 host） | `./deploy host-infra` |
| Relay（QUIC） | `./deploy relay` |
| iOS IPA | `./deploy ios` |
| macOS 桌面包 | `./deploy desktop` |
| 状态 | `./deploy status` |
| 新鲜部署烟测 | `./deploy fresh-smoke [epoch]` |
| 日志 | `./deploy logs [gateway\|cortex\|runtime\|worker\|subscriber\|relay]` |

## 行为说明

- **Docker Compose 执行层**：后端和 Factory 都由 Compose 管理；Release Controller 负责 build/push/deploy 编排，`deploy` 只负责在控制器授权下执行 image-based namespace deploy。生产机不 build，部署使用 digest 或 `sha-<hex>` tag。
- **Release Controller CI/CD**：
  - 当前控制面：API host Docker Compose project `novaic-release-controller`。
  - 本机 API：`http://127.0.0.1:19880`。
  - 正规开发流：开发机先跑聚焦单元测试做快速反馈；push/merge 后由 Release Controller 的 `quality_gates` 做权威 staging 准入；staging deploy 后再跑 smoke/integration；prod 只 promote 已通过 staging 的不可变镜像，不从 branch 直接发布。
  - 健康检查：`curl -fsS http://127.0.0.1:19880/health`。
  - 状态检查：`curl -fsS http://127.0.0.1:19880/v1/status`。
  - 手动 trigger：`POST /v1/triggers`；省略 `dry_run` 就是真实执行。需要只观察时显式传 `dry_run=true`。
  - branch polling dry-run：`POST /v1/polls/once`，请求体 `{"dry_run": true}`。
  - autonomous polling：`polling_enabled=true` 时服务启动后每 `poll_interval_seconds` 自动 poll；polling 默认真实执行，只有显式请求 `dry_run=true` 才是观察模式。
  - executor check：`docker exec novaic-release-controller-release_controller-1 docker --version`、`docker exec novaic-release-controller-release_controller-1 docker compose version`、`docker exec novaic-release-controller-release_controller-1 ssh -o BatchMode=yes root@api.gradievo.com true` 必须成功。
  - inspect：`curl -fsS http://127.0.0.1:19880/v1/status`，看 `polling.enabled`、`polling.running`、`polling.iteration_count`、`polling.last_error`、`recent_runs`。
  - pause：把 `/opt/novaic/release-controller/config.json` 里的 `polling_enabled` 改成 `false`，再执行 `./deploy release-controller-image <当前digest>`。
  - enable：把 `polling_enabled` 改成 `true`；如需临时观察/计划，调用 trigger/poll 时显式传 `dry_run=true`。
  - quality gate rule：`quality_gates` 是 branch release 的 CI 门禁，运行在 checkout/submodule update 之后、image build 之前；失败会阻断 build/deploy，并把 run 标成 failed。
  - verify command rule：`deploy.verify_commands` 必须能在 release-controller 容器内执行；只放轻量 release preflight，例如 `bash -n deploy` 和配置/编译检查。不要把它当第二套 CI，也不要放依赖本机 venv 的整仓测试。
  - prod promotion：`POST /v1/promotions/prod`，只接收 digest 或 `sha-<hex>` tag。
  - rollback：`POST /v1/rollbacks/<namespace>`，使用 previous pointer。
  - prod guard：branch release 默认执行只适用于非 prod 命名空间；prod 仍不通过 branch 触发，只能走 promotion/rollback API。
  - prod smoke：Release Controller 使用 `https://api.gradievo.com/health` 作为公网 ingress smoke；`https://api.gradievo.com/api/health` 当前需要认证会返回 401，本地应用健康用 `127.0.0.1:19999/api/health` 单独核验。
  - worktree repair：在 API host 执行 `cd /opt/novaic/release-controller/worktree && git pull --ff-only origin main && git submodule update --init --recursive -- Entangled novaic-agent-runtime novaic-blob-service novaic-business novaic-common novaic-cortex novaic-device novaic-gateway novaic-logicalfs novaic-sandbox-service novaic-llm-factory`。
- **内部执行器 guard**：`deploy services-image <namespace> <image-ref>` 和 `deploy factory-image <namespace> <image-ref>` 只允许 Release Controller 传入 `NOVAIC_DEPLOY_CALLER=release-controller`、run id、namespace 和 commit 后执行；人工直接调用会在连接远端前失败。
- **`deploy host-infra`**：同步 `docker/host-infra` Compose 包，构建 `novaic/quic-service:local`，迁移 Redis RDB 和 coturn 运行时配置，停止并禁用宿主机 `redis-server` / `coturn` / `novaic-quic-service`，启动 Docker Compose，验证 Redis/coturn/QUIC 端口归属 Docker 后清理 host 残留，包括旧 `/opt/novaic/start.sh`、`/opt/novaic/services` 和 API-host QUIC 目录。nginx 保留 host 管理。
- **`deploy services-image <namespace> <image-ref>`**：Release Controller 内部执行器。同步 `docker/api-backend` Compose 包和配置快照，生成 namespace env（如 `/opt/novaic/docker/api-backend.staging.env`），执行 `docker compose pull`，先启动并等待 `service-registry` 健康，再执行全量 `docker compose up -d --no-build --remove-orphans`。如果 Compose 在重建同 namespace project 时留下不一致容器状态，执行器会清理该 namespace 的 Compose project 后用同一不可变 image 重试一次；它不会清理其他 namespace。生产机不 build；`image-ref` 必须是 digest 或 sha tag，拒绝 `latest` / `local` / generic tag。
- **`deploy release-controller-image <image-ref>`**：中心化 CD 控制面部署路径。同步 `docker/release-controller` Compose 包到 `/opt/novaic/docker/release-controller/`，使用 `/opt/novaic/release-controller/config.json`、`/opt/novaic/release-controller/state/` 和 `/opt/novaic/release-controller/worktree/`，执行 `docker compose pull` 和 `docker compose up -d --no-build release_controller`。只绑定 `127.0.0.1:19880`，不配置 Nginx public ingress；`image-ref` 必须是 digest 或 sha tag。
- **已关闭的后端手动路径**：`deploy services`、`deploy api-backend`、`deploy services-legacy`、legacy 单服务目标、`deploy factory`、`deploy all` 都会失败，错误会指向 Release Controller。
- Compose 主路径目录：
  - Host infra Compose 包：**`/opt/novaic/docker/host-infra/`**
  - Host infra 运行 env：**`/opt/novaic/docker/host-infra.env`**（0600，不提交）
  - Host infra runtime 数据：**`/opt/novaic/host-infra/`**
  - Host infra 清理备份：**`/opt/novaic/backups/host-infra-cleanup-*`**
  - Compose 包：**`/opt/novaic/docker/api-backend/`**
  - namespace env：**`/opt/novaic/docker/api-backend.<namespace>.env`**（0600，不提交）
  - Release Controller Compose 包：**`/opt/novaic/docker/release-controller/`**
  - Release Controller runtime：**`/opt/novaic/release-controller/`**
- **LLM Factory（API host Docker）**：`./deploy factory-image <namespace> <image-ref>` 是 Release Controller 内部执行器，同步 `docker/llm-factory` Compose 包，生成 `/opt/novaic/llm-factory/<namespace>/compose.env`，执行 `docker compose pull` 和 `docker compose up -d --no-build`。prod 监听 `127.0.0.1:19990`，staging 监听 `127.0.0.1:29990`。
- **外部依赖**：Postgres 容器在 `127.0.0.1:5432`；Redis 由 Host infra Docker 提供在 `127.0.0.1:6379`；coturn 和 QUIC relay 也由 Host infra Docker 管理。宿主机长期裸跑例外只有 nginx。
- `./deploy status` 先输出 Docker Compose 服务状态，再输出 legacy/live port audit。
- `./deploy logs <svc>` 优先读取 Compose logs；如果 Compose 包尚未安装，才回退到旧日志文件。
- `fresh-smoke` 仍是 timestamp-aware 的旧日志 mtime 检查；它以传入 epoch 作为重启前边界，避免旧日志被误判为本次启动结果。Compose cutover 后以 Compose health/status 为准。
- `./deploy status` 的 legacy/live port audit 仍通过 `runtime_worker_roster.py`（runtime_roster.py contract）输出 role-level required runtime subprocesses，包括 `task-worker control`、`session-outbox-worker`、`subscriber.log` 等检查标签；这只是观测，不是发布入口。

## 相关

- 总览与排障：**[`HANDOVER.md`](../../HANDOVER.md)**（根目录）。
- 架构与端口：**[`../architecture/overview.md`](../architecture/overview.md)**。
