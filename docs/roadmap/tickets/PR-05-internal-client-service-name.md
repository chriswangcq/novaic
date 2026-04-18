# PR-05  `internal_client(service_name=...)` 必填 + 自动注身份头

| 字段 | 值 |
| --- | --- |
| **Phase** | 1（合约对齐） |
| **Milestone** | M1 |
| **承诺** | R7 |
| **Status** | `[ ]` |
| **Depends on** | — |
| **Blocks** | PR-06, PR-08, PR-10, PR-12 |
| **估时** | 0.5 d |
| **Owner** | __ |
| **PR 标题** | `refactor(common): internal_client requires service_name; auto-inject X-Internal-Service` |

## 目标

把"调用方身份"做成默认行为，消除 hihi 事件里 HealthWorker 裸 `httpx.Client()` → `/recover/all` 401 的 bug 类别。

## 范围

- `novaic-common/common/http/clients.py`
- 所有现有 `internal_client(` 调用点（逐个迁移）

## 前置 Checklist

- [ ] `rg 'internal_client\(' novaic-*/' > /tmp/callsites.txt` — 清点所有调用点
- [ ] 与 PR-04 协调：PR-04 的 allowlist 应当在本 PR 合并后逐个删除对应行

## 实施 Checklist

### 1. 升级 `internal_client` 签名

- [ ] `clients.py` 中 `internal_client(...)` 新增 `service_name: str` 必填参数
- [ ] 请求头自动注入：
  - `X-Internal-Key: <env NOVAIC_INTERNAL_KEY>`
  - `X-Internal-Service: <service_name>`
  - `User-Agent: novaic-internal/<service_name>`（可选）
- [ ] 若 `service_name` 为空串或 None → 立即 `raise ValueError("service_name required")`（fail-fast）
- [ ] 若 `NOVAIC_INTERNAL_KEY` 未设置 → 启动期 log WARN（目标服务侧 auth 会拒，不在 client 侧硬拒避免死链）

### 2. 迁移现有调用点

按 `/tmp/callsites.txt` 逐个迁移：
- [ ] `novaic-business/...`
- [ ] `novaic-agent-runtime/...`（尤其 `health_worker_sync.py` 的两处裸 `httpx.Client()` → 见 PR-12）
- [ ] `novaic-cortex/...`
- [ ] `novaic-gateway/...`
- [ ] `novaic-device/...`

每处迁移：
- [ ] 旧 `internal_client(base_url=..., ...)` → 新 `internal_client(service_name="<my-service>", base_url=..., ...)`
- [ ] 裸 `httpx.Client()` / `httpx.AsyncClient()` → 如果是内部调用，改 `internal_client(...)`

### 3. 过渡期兼容

- [ ] **不**保留 `service_name` 可选 overload；PR-04 的 CI 已有 allowlist 兜底迁移期；一次到位更干净
- [ ] 若团队需要灰度，可在 `clients.py` 里 warning 一个 release 后 raise

## 测试 Checklist

- [ ] 单测 `tests/test_internal_client.py`:
  - [ ] 无 service_name → ValueError
  - [ ] 默认注入 `X-Internal-Service`
  - [ ] `NOVAIC_INTERNAL_KEY` 未设置 → WARN + 继续
- [ ] 手工：启 Cortex + Queue Service，任一内部调用 → 目标服务日志应能看到 `caller=` 字段（PR-06 会消费这个头）

## 可观测性 Checklist

- [ ] 客户端本地 log：`[internal_client] service=<name> → <url>`（DEBUG 级，不要刷屏）

## 文档 Checklist

- [ ] [message-wake-refactor.md](../message-wake-refactor.md) P1-1 → `[x]`
- [ ] 本工单 Status → `[x]`
- [ ] 更新 [docs/architecture/authentication.md](../../architecture/authentication.md)：加"内部调用身份"一节

## 验收命令

```bash
# 全仓搜索
rg "internal_client\(" novaic-*/ | rg -v "service_name="
# 预期：空（除了 clients.py 本体定义 / tests）
```

```bash
# 启动 + 手调
curl -H "X-Internal-Key: $NOVAIC_INTERNAL_KEY" -H "X-Internal-Service: test" \
     http://localhost:7000/api/queue/recover/all
# 预期 200
```

## 回滚

`git revert` — 若生产紧急，revert 后只保留 `X-Internal-Key` 注入；`X-Internal-Service` 消费端（PR-06）本来就只做 log，不硬依赖。

## 备注

- **关键**：本 PR 合并后立即开 PR-06（服务端消费这个头），否则看不到灰度效果。
- `service_name` 取值建议：`business`、`cortex`、`runtime`、`gateway`、`device`、`scheduler`、`health`、`subscriber`（保持短小、稳定）。
