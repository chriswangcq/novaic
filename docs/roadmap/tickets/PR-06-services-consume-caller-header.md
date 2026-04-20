# PR-06  服务端消费 `X-Internal-Service`（access log 带 caller）

| 字段 | 值 |
| --- | --- |
| **Phase** | 1 |
| **Milestone** | M1 |
| **承诺** | R7 |
| **Status** | `[x]` |
| **Depends on** | PR-05 |
| **Blocks** | — |
| **估时** | 0.5 d |
| **Owner** | __ |
| **PR 标题** | `feat(auth): services parse X-Internal-Service for access log attribution` |

## 目标

让 "谁调了我" 成为所有服务端日志的一等字段，断 hihi 那类"静默被 deny 却不知道调用方是谁"的类别 bug。

## 范围

- `novaic-cortex/novaic_cortex/auth.py` (或等价中间件)
- `novaic-agent-runtime/queue_service/auth.py`
- `novaic-business/business/internal/auth.py`
- `novaic-gateway/gateway/infra/auth.py`
- `novaic-device/...` 的内部认证点

## 前置 Checklist

- [x] PR-05 合并 + 各服务重启一次，客户端已在发送 `X-Internal-Service`

## 实施 Checklist

### 每个服务的 auth middleware

- [x] 读取 `request.headers.get("X-Internal-Service")`（缺失时 `caller="unknown"`）
- [x] **不做 401**（灰度期）；后续（PR-19 后）可考虑 WARN 级 → ERROR 级 → deny
- [x] 绑到 request scope / contextvar：
  ```python
  request.state.caller = caller
  ```
- [x] Access log formatter 追加字段：
  ```
  method=... path=... status=... caller=<service_name> internal=1
  ```

### 服务内部 RPC 分摊

- [x] 各服务若有内部消息总线 / worker → 把 `caller` 也透传到 log（方便排查 "是 Saga worker 还是 scheduler worker 打过来的"）

### 缺失策略

- [x] 内部端点收到 `X-Internal-Key` 但无 `X-Internal-Service` → WARN 级日志 `internal_caller_unknown path=...`（gate 转换成 deny 的条件在 PR-19 完成后另开一个 cleanup PR）

## 测试 Checklist

- [x] 单测：auth middleware 解析 `X-Internal-Service` → `request.state.caller`
- [x] 手工：三种身份调 Queue Service `/recover/all`：
  - Cortex → 日志 `caller=cortex`
  - Runtime HealthWorker → 日志 `caller=runtime-health`
  - 无头（curl 直调）→ 日志 `caller=unknown + WARN`

## 可观测性 Checklist

- [x] metric `internal_requests_total{caller, target, status}` counter — 落地于 PR-32（零依赖 registry；在 `common/http/clients.py` 的 response event-hook 统一打点）
- [x] 访问日志固定输出 `caller=` 字段

## 文档 Checklist

- [x] [message-wake-refactor.md](../message-wake-refactor.md) P1-2 → `[x]`
- [x] 本工单 Status → `[x]`
- [x] 更新 [docs/architecture/authentication.md](../../architecture/authentication.md)：补一节 "内部调用的 caller 归因"

## 验收命令

```bash
tail -f business.log | rg 'caller='       # 看到 caller 字段
tail -f queue-service.log | rg 'caller='  # 同上
# 手工裸 curl 无 X-Internal-Service
curl -H "X-Internal-Key: $KEY" http://localhost:7000/api/queue/recover/all
# 日志里 caller=unknown + WARN
```

## 回滚

`git revert` — 纯 log 字段 + contextvar，无业务语义。

## 备注

- 不要在本 PR 里做 "无 caller 就 401"；那是 PR-19 之后的事。
- 对应 OBS-1（全 Phase 基线项），本 PR 是 OBS-1 的第一次落地。
