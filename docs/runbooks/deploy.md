# 部署（Runbook）

父仓库根目录 **`deploy`** 为统一部署入口：本地 **rsync** 到远端，API 后端主路径由服务器上的 **Docker Compose** 管理（不在本机 `nohup` 长期跑）。

> **原理、Gateway/Relay/Factory 主机表、OTA 三处同步、维护命令** 的完整版见 [**`cloud-production.md`**](cloud-production.md)。本节为命令速查。

细节以仓库内 **`./deploy` 源码**为准。

## 前置

- 已配置对 **`api.gradievo.com`**、**relay** 等的 SSH（脚本内写死主机别名，见 `deploy` 顶部变量）；LLM Factory 当前也在 API host Docker 上。
- 子模块目录存在且可同步（如 `novaic-gateway`、`novaic-app`）。
- Release Controller 是长期 CI/CD 主路径，当前运行在 API host 的 `127.0.0.1:19880`，不走公网 Nginx。
- GitHub Actions 只作为过渡期验证/fallback；不要把它当作长期发布编排中心。

## 常用命令

| 目标 | 命令 |
|------|------|
| 前端 OTA | `./deploy frontend [version]`（默认版本见脚本内 `VERSION`） |
| 全部 API 后端（不可变镜像 CD 主路径） | `./deploy services-image staging <image-ref>` / `./deploy services-image prod <image-ref>` |
| Release Controller（中心化 CD 控制面） | `./deploy release-controller-image <image-ref>` |
| 全部 API 后端（Docker Compose 远端 build 回退） | `./deploy services` 或 `./deploy api-backend` |
| Host infra（Redis/coturn/QUIC Docker，nginx 保留 host） | `./deploy host-infra` |
| 回滚到旧 host venv/start.sh 路径 | `./deploy services-legacy` |
| legacy 单个后端（仍会触发旧路径**全量**远端重启） | `./deploy runtime` / `./deploy cortex` / `./deploy blob-service` 等 |
| Relay（QUIC） | `./deploy relay` |
| LLM Factory（不可变镜像 CD 主路径） | `./deploy factory-image staging <image-ref>` / `./deploy factory-image prod <image-ref>` |
| LLM Factory（API host Docker 远端 build 回退） | `./deploy factory` |
| iOS IPA | `./deploy ios` |
| macOS 桌面包 | `./deploy desktop` |
| 一键：前端 + 全后端 + relay + iOS + 桌面 | `./deploy all [version]` |
| 状态 | `./deploy status` |
| 新鲜部署烟测 | `./deploy fresh-smoke [epoch]` |
| 日志 | `./deploy logs [gateway\|cortex\|runtime\|worker\|subscriber\|relay]` |

## 行为说明

- **Docker Compose 主路径**：后端和 Factory 都由 Compose 管理；长期 CD 主路径是 image-based namespace deploy，远端 build 只作为回退。
- **Release Controller CI/CD**：
  - 当前控制面：API host Docker Compose project `novaic-release-controller`。
  - 本机 API：`http://127.0.0.1:19880`。
  - 健康检查：`curl -fsS http://127.0.0.1:19880/health`。
  - 状态检查：`curl -fsS http://127.0.0.1:19880/v1/status`。
  - 手动 dry-run trigger：`POST /v1/triggers`，例如 branch `main` + commit + `dry_run=true`。
  - branch polling dry-run：`POST /v1/polls/once`，请求体 `{"dry_run": true}`。
  - autonomous polling：`polling_enabled=true` 时服务启动后每 `poll_interval_seconds` 自动 poll；当前线上为 `enabled=true`、`dry_run_default=true`。
  - executor check：`docker exec novaic-release-controller-release_controller-1 docker --version`、`docker exec novaic-release-controller-release_controller-1 docker compose version`、`docker exec novaic-release-controller-release_controller-1 ssh -o BatchMode=yes root@api.gradievo.com true` 必须成功。
  - inspect：`curl -fsS http://127.0.0.1:19880/v1/status`，看 `polling.enabled`、`polling.running`、`polling.iteration_count`、`polling.last_error`、`recent_runs`。
  - pause：把 `/opt/novaic/release-controller/config.json` 里的 `polling_enabled` 改成 `false`，再执行 `./deploy release-controller-image <当前digest>`。
  - enable：把 `polling_enabled` 改成 `true`；保持 `dry_run_default=true` 可只观察/计划，不执行 build/deploy。
  - verify command rule：`deploy.verify_commands` 必须能在 release-controller 容器内执行；不要放依赖本机 venv 的整仓测试。完整测试放 builder/CI，controller 负责 release preflight + image build/import smoke + deploy。
  - prod promotion：`POST /v1/promotions/prod`，只接收 digest 或 `sha-<hex>` tag。
  - rollback：`POST /v1/rollbacks/<namespace>`，使用 previous pointer。
  - 当前限制：`dry_run_default=true`；真实 non-dry-run branch release 是显式运行策略变更，不通过 prod branch 触发。
  - worktree repair：在 API host 执行 `cd /opt/novaic/release-controller/worktree && git pull --ff-only origin main && git submodule update --init --recursive -- Entangled novaic-agent-runtime novaic-blob-service novaic-business novaic-common novaic-cortex novaic-device novaic-gateway novaic-logicalfs novaic-sandbox-service novaic-llm-factory`。
- **GitHub Actions fallback**：旧 workflow 可继续做验证和镜像构建参考，但长期不作为发布编排中心。
- **`deploy host-infra`**：同步 `docker/host-infra` Compose 包，构建 `novaic/quic-service:local`，迁移 Redis RDB 和 coturn 运行时配置，停止并禁用宿主机 `redis-server` / `coturn` / `novaic-quic-service`，启动 Docker Compose，验证 Redis/coturn/QUIC 端口归属 Docker 后清理 host 残留，包括旧 `/opt/novaic/start.sh`、`/opt/novaic/services` 和 API-host QUIC 目录。nginx 保留 host 管理。
- **`deploy services-image <namespace> <image-ref>`**：CI/CD 主路径。同步 `docker/api-backend` Compose 包和配置快照，生成 namespace env（如 `/opt/novaic/docker/api-backend.staging.env`），执行 `docker compose pull` 和 `docker compose up -d --no-build --remove-orphans`。生产机不 build；`image-ref` 必须是 digest 或 sha tag，拒绝 `latest` / `local` / generic tag。
- **`deploy release-controller-image <image-ref>`**：中心化 CD 控制面部署路径。同步 `docker/release-controller` Compose 包到 `/opt/novaic/docker/release-controller/`，使用 `/opt/novaic/release-controller/config.json`、`/opt/novaic/release-controller/state/` 和 `/opt/novaic/release-controller/worktree/`，执行 `docker compose pull` 和 `docker compose up -d --no-build release_controller`。只绑定 `127.0.0.1:19880`，不配置 Nginx public ingress；`image-ref` 必须是 digest 或 sha tag。
- **`deploy services` / `deploy api-backend`**：远端 build 回退路径。先确认 Host infra Docker 已运行，再同步 `docker/api-backend` Compose 包和 build context，构建 `novaic/api-backend:local` 镜像，生成 `/opt/novaic/docker/api-backend.env`，执行 `docker compose config`，停止旧 host-process 后端，再执行 `docker compose up -d --remove-orphans`。
- Compose 主路径目录：
  - Host infra Compose 包：**`/opt/novaic/docker/host-infra/`**
  - Host infra 运行 env：**`/opt/novaic/docker/host-infra.env`**（0600，不提交）
  - Host infra runtime 数据：**`/opt/novaic/host-infra/`**
  - Host infra 清理备份：**`/opt/novaic/backups/host-infra-cleanup-*`**
  - Compose 包：**`/opt/novaic/docker/api-backend/`**
  - 运行 env：**`/opt/novaic/docker/api-backend.env`**（0600，不提交）
  - namespace env：**`/opt/novaic/docker/api-backend.<namespace>.env`**（0600，不提交）
  - build context：**`/opt/novaic/docker-builds/api-backend/`**
  - Release Controller Compose 包：**`/opt/novaic/docker/release-controller/`**
  - Release Controller runtime：**`/opt/novaic/release-controller/`**
- **LLM Factory（API host Docker）**：`./deploy factory-image <namespace> <image-ref>` 是 CD 主路径，同步 `docker/llm-factory` Compose 包，生成 `/opt/novaic/llm-factory/<namespace>/compose.env`，执行 `docker compose pull` 和 `docker compose up -d --no-build`。prod 监听 `127.0.0.1:19990`，staging 监听 `127.0.0.1:29990`。`./deploy factory` 保留为远端 build 回退路径，同步 `novaic-llm-factory` app 与 Compose 包后 build/up。
- **外部依赖**：Postgres 容器在 `127.0.0.1:5432`；Redis 由 Host infra Docker 提供在 `127.0.0.1:6379`；coturn 和 QUIC relay 也由 Host infra Docker 管理。宿主机长期裸跑例外只有 nginx。
- **`deploy services-legacy`** 是短期回滚入口：同步旧 host venv 目录并执行 `/opt/novaic/start.sh`。不要把它当作新主路径。
- **Owner/removal gate**：P006 cleanup 负责在 Compose 验证完成后归档/移除旧 host-process 残留；`services-legacy` 只保留为显式回滚路线。
- `./deploy status` 先输出 Docker Compose 服务状态，再输出 legacy/live port audit。
- `./deploy logs <svc>` 优先读取 Compose logs；如果 Compose 包尚未安装，才回退到旧日志文件。
- `fresh-smoke` 仍是 timestamp-aware 的旧日志 mtime 检查，主要用于 legacy 回滚路径：它以重启前 epoch 作为边界，避免旧日志被误判为本次启动结果；Compose cutover 后以 Compose health/status 为准。
- legacy `scripts/start.sh` 仍保留 required runtime subprocesses / role-level 检查，只用于回滚时确认 `task-worker control`、`session-outbox-worker`、`subscriber.log` 等 runtime roles；角色定义来源是 `runtime_roster.py`。

## 相关

- 总览与排障：**[`HANDOVER.md`](../../HANDOVER.md)**（根目录）。
- 架构与端口：**[`../architecture/overview.md`](../architecture/overview.md)**。
