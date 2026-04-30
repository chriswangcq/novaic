# PR-121 — Gateway Entangled Sync Endpoint Discovery Boundary

| Field | Value |
| --- | --- |
| Status | `[✓] deployed 2026-04-30` |
| Scope | `novaic-gateway`, `scripts/start.sh`, docs/guardrails |
| Goal | Gateway 对 Entangled 的依赖只保留一个明确边界：给客户端发现 direct sync WebSocket endpoint。 |
| Non-goal | 不改 Business / Subscriber 对 Entangled HTTP 的真实数据消费路径。 |

## 背景

Gateway 当前仍有两类 Entangled 耦合：

1. `main_gateway.py --entangled-url` 接收 HTTP base URL，并写入 `ServiceConfig.ENTANGLED_URL / ENTANGLED_SERVICE_URL / HOST / PORT`。
2. Gateway 本地 auth entity metadata 复用 `entangled.sql.field_def` / `SqlEntityDef`，导致 Gateway 运行时需要把 `Entangled/packages/server-python` 塞进 `sys.path`。

这两者都超出了 Gateway 的职责。Gateway 应只是 thin edge：auth、AppWS、file proxy、internal auth。本票把 Entangled 相关依赖收口为 **sync endpoint discovery**，并把本地 auth schema 类型改为 Gateway 自己的极小 metadata。

## 设计

- Gateway CLI 改为接收 `--entangled-sync-ws-url`，只用于 AppWS 下发 `entangledWsUrl`。
- `gateway/infra/entangled_ws.py` 只读取 `ServiceConfig.ENTANGLED_PUBLIC_WS_URL`，不再从 `ENTANGLED_URL` 推导。
- `scripts/start.sh` 自己从端口拼出 `ws://127.0.0.1:19900/v1/sync` 传给 Gateway；Business / Subscriber 继续使用 `--entangled-url`。
- Gateway `gateway/entity/store.py` 内置最小 `FieldKind / FieldDef / F / EntityDef`，只服务 local-only auth entities。
- 移除 Gateway `sys.path` 注入 Entangled server-python、pytest/pyright 对 Entangled 的额外路径、历史 `patch.diff`。

## 实施 Checklist

- [x] 更新 Gateway CLI 参数和 `scripts/start.sh` 启动参数。
- [x] 简化 endpoint discovery：只消费 public WS URL。
- [x] 移除 Gateway 对 Entangled schema 类型库的 import / sys.path / test path 依赖。
- [x] 更新 Gateway entity docs，明确非 auth entity 通过 Business 边界。
- [x] 删除 `novaic-gateway/patch.diff` 历史补丁残片。

## 单元测试 / Guardrail

- [x] 新增 Gateway guardrail：活代码不得使用 `--entangled-url`、`ServiceConfig.ENTANGLED_URL`、`ENTANGLED_SERVICE_URL`、`host_port_from_http_url`。
- [x] 新增 Gateway guardrail：活代码不得 import `entangled.*`、不得引用 `SqlEntityDef`、不得注入 `Entangled/packages/server-python`。
- [x] 保留/更新 AppWS endpoint-only 测试。
- [x] 运行 `cd novaic-gateway && python -m pytest`。
- [x] 运行 `cd novaic-gateway && python -m compileall -q gateway`。
- [x] 运行 `bash -n scripts/start.sh`。

## 冒烟测试

- [x] 启动脚本静态检查确认 Gateway 只接收 `--entangled-sync-ws-url`。
- [x] 本地/生产日志确认 Gateway 启动正常，AppWS 可下发 `entangled_endpoint`。
- [x] 确认 Business / Subscriber 的 `--entangled-url` 仍保留。

## 部署 Checklist

- [x] 子仓 `novaic-gateway` commit + push。
- [x] 父仓 `scripts/start.sh` + submodule bump commit + push。
- [x] 执行 `./deploy gateway`。
- [x] `./deploy status` 通过。
- [x] 线上代码 grep：Gateway 无旧 Entangled HTTP/schema 类型依赖；启动参数为 `--entangled-sync-ws-url`。

## 线上证据

- `./deploy status`: Entangled/Gateway/Business/Device/Queue/File/Cortex 全部监听，Workers 8 进程。
- 远程 guardrail: `/opt/novaic/services/novaic-gateway` 活代码无 `--entangled-url`、`ServiceConfig.ENTANGLED_URL`、`ENTANGLED_SERVICE_URL`、`from entangled`、`SqlEntityDef`、`Entangled/packages/server-python`。
- 远程 `start.sh` Gateway block: 只包含 `--entangled-sync-ws-url "$ENTANGLED_SYNC_WS_URL"`，且 Gateway PYTHONPATH 不再包含 Entangled server-python。
- Gateway health: `GET http://127.0.0.1:19999/api/health` 返回 `status=healthy`。

## Github 提交

- Gateway commit: `chore(gateway): narrow entangled dependency to sync discovery`
- Parent commit: `chore: bump gateway for entangled sync discovery boundary`
