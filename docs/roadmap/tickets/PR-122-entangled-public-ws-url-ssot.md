# PR-122 — Entangled Public WebSocket URL SSOT

| Field | Value |
| --- | --- |
| Status | `[✓] deployed 2026-04-30` |
| Scope | `scripts/start.sh`, `novaic-gateway`, docs/guardrails |
| Goal | `services.entangled_service.public_ws_url` 是客户端 Entangled sync WebSocket 的唯一来源；Gateway 只读取并转发，不再通过 CLI 或端口拼接生成。 |
| Non-goal | 不改变 Business / Subscriber 对 Entangled 内部 HTTP URL 的消费路径。 |

## 背景

PR-121 把 Gateway 与 Entangled 的关系收口为 sync endpoint discovery，但仍在 `scripts/start.sh` 中从内部端口拼出 `ws://127.0.0.1:19900/v1/sync`，再通过 `--entangled-sync-ws-url` 注入 Gateway。

这会把服务器 loopback 地址下发给桌面客户端，导致 App 直连 Entangled WS 失败，消息停在 `Sending...`。根因不是 Subscriber，也不是 outbox；用户消息没有到达服务器。

## 设计

- 保留两条不同语义：
  - `services.entangled_service.url`: 服务端内部 HTTP，只给 Business / Subscriber。
  - `services.entangled_service.public_ws_url`: 客户端可达 WS，只给 Gateway AppWS 下发。
- 删除 Gateway `--entangled-sync-ws-url` CLI 参数和 `scripts/start.sh` 对 sync WS 的派生变量。
- Gateway 启动时读取 `ServiceConfig.ENTANGLED_PUBLIC_WS_URL` 并 fail-fast 校验：
  - 必须存在。
  - 必须是 `ws://` 或 `wss://`。
  - 必须有 host。
  - host 不得是 localhost / loopback / bind-all / link-local。
  - path 必须是 `/entangled/v1/sync`。
- AppWS 仍只下发 `entangledWsUrl`，schema 和数据同步继续由 Entangled WS 负责。

## 实施 Checklist

- [x] 删除 `scripts/start.sh` 中 `ENTANGLED_SYNC_WS_URL` 和 Gateway `--entangled-sync-ws-url` 参数。
- [x] 删除 `novaic-gateway/main_gateway.py` 中对应 CLI 参数和 `ServiceConfig.ENTANGLED_PUBLIC_WS_URL` 覆盖逻辑。
- [x] 在 Gateway 启动期校验 `public_ws_url`，配置错误直接启动失败。
- [x] 更新 Gateway guardrail，禁止重新引入 CLI sync WS 注入或内部端口派生。
- [x] 更新 PR-121 文档，说明 CLI 注入被本票取代。

## 单元测试 / Guardrail

- [x] Gateway 单测覆盖：缺失 `public_ws_url` fail-fast。
- [x] Gateway 单测覆盖：loopback / localhost / 错 path / 非 WS scheme 被拒绝。
- [x] Gateway 单测覆盖：`wss://api.gradievo.com/entangled/v1/sync` 被接受。
- [x] Guardrail 覆盖：`start.sh` 不得出现 `ENTANGLED_SYNC_WS_URL` 或 Gateway `--entangled-sync-ws-url`。
- [x] 运行 `cd novaic-gateway && python -m pytest -q`。
- [x] 运行 `cd novaic-gateway && python -m compileall -q gateway main_gateway.py`。
- [x] 运行 `bash -n scripts/start.sh`。

## 冒烟测试

- [x] 部署后查看 Gateway 日志，确认 `EntangledWS` client sync endpoint 为 `wss://api.gradievo.com/entangled/v1/sync`。
- [x] 线上 Gateway health 返回 `status=healthy`。
- [x] 线上 grep 确认 Gateway 启动参数不再有 sync WS CLI。

## 部署 / Github

- [x] 子仓 `novaic-gateway` commit + push。
- [x] 父仓 `scripts/start.sh`、docs、submodule bump commit + push。
- [x] 执行 `./deploy gateway`。
- [x] `./deploy status` 通过。

## 验证记录

- `cd novaic-gateway && python -m pytest -q`: `18 passed`。
- `cd novaic-gateway && python -m compileall -q gateway main_gateway.py`: passed。
- `bash -n scripts/start.sh`: passed。
- `./deploy gateway`: 全栈重启成功。
- `./deploy status`: Entangled/Gateway/Business/Device/Queue/File/Cortex 全部监听，Workers 8 进程。
- 远程 Gateway 日志：`[EntangledWS] validated client sync endpoint: wss://api.gradievo.com/entangled/v1/sync`。
- 远程 Gateway block：无 `--entangled-sync-ws-url`。
- 远程活代码 grep：无 `ENTANGLED_SYNC_WS_URL` / `--entangled-sync-ws-url`。
- Gateway commit: `fix(gateway): use config public entangled sync endpoint` (`50fd37d`)。
- Parent commit: `fix: use public entangled sync endpoint from config`。
