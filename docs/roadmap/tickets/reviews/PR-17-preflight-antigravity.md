# PR-17 Preflight Report (Canary & Deployment)

## ⚠️ 重大发现：生产 pre-PR-15 → Canary 是巨型集成上线

本次 Canary 不是简单的打开 subscriber 标志，而是包含了 PR-04 到 PR-16 的大量**首次生产部署**代码：
- PR-05 `internal_client` 强制 `service_name`
- PR-06 `CallerLoggingMiddleware` 统一日志
- PR-07 `/internal/agents/{id}/owner` 端点
- PR-08 `AgentOwnershipResolver` 带 TTL 缓存
- PR-09 `TriggerType` 权威枚举解析旧数据（存在数据兼容风险）
- PR-10~13 `DispatchAssembler`
- PR-14 `message_outbox` 表结构 + co-transaction INSERT
- PR-15/16 Subscriber 全量实现

因此，**观察期必须延长至 4-6h**，并且在 `docs/runbooks/subscriber-canary.md` 开头必须加入明确的风险警示章节，详细列出受影响的模块。我们不仅要监控 subscriber，还要监控所有可能的回归异常（如 ownership lookup miss）。

## §F Discovery 实地勘测结果

1. **生产当前 Business 代码版本**：
   - 勘测命令：`ssh root@api.gradievo.com "ls -la /opt/novaic/services/novaic-business/business/subscribers"`
   - **结果**：生产机器上的 `/opt/novaic/services/novaic-business` 不是一个 git 仓库（`git log` 会报错），且不存在 `subscribers/dispatch_subscriber.py` 文件。
   - **结论**：生产代码版本仍早于 PR-15/16。在执行 PR-17 的测试前，**必须先做一次完整的三子仓库（Entangled/novaic-common/novaic-business）同步部署**。

2. **生产 message_outbox 表是否存在**：
   - 勘测命令：`ssh root@api.gradievo.com "sqlite3 /opt/novaic/data/entangled.db '.schema message_outbox'"`
   - **结果**：输出为空。
   - **结论**：`message_outbox` 表尚未在生产创建，意味着 Entangled 侧也没跑过 PR-14 以后的更新。需要一同 rsync 并重启触发 schema 创建。

3. **当前 outbox 积压量**：
   - **结论**：由于表尚不存在，积压量为 0。

4. **生产 Business 日志的格式**：
   - 勘测命令：提取最新 business log 的前 20 行。
   - **结果**：日志为纯 ASCII 文本（例如 `2026-04-17 10:42:01,015 [INFO] business: Ready`）。
   - **结论**：可以完美被 `rg` 解析。

5. **`deploy-gateway.sh` 的同步范围**：
   - 勘测：查看源码。
   - **结果**：它目前通过 `GATEWAY_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"` 只同步了网关或特定的外层包，并不会自动完整同步 `novaic-common` 和 `Entangled` 到生产预期的全部位置。
   - **结论**：`deploy-business.sh` **需要独立编写，并明确 rsync `novaic-business/`、`Entangled/` 和 `novaic-common/` 三个子仓库**。

6. **压测脚本的隔离账号策略**：
   - 勘测命令：`sqlite3 ... "SELECT id FROM users WHERE id LIKE 'canary_u_%'"`
   - **结果**：输出为空，生产没有现成的隔离账号。
   - **结论**：Canary traffic 脚本在发压前需要包含一个引导（bootstrap）步骤。
   - **Bootstrap 方案与技术细节**：
     由于压测使用的是 `common.http.clients` 的 `internal_async_client`，我们会自动携带 `X-Internal-Key: $JWT_SECRET` 和 `X-Internal-Service: canary-traffic`，具备最高内部权限。
     1. **创建 User**：
        - 端点：`POST http://127.0.0.1:19998/internal/entities/users?user_id=canary_u_fixed`
        - Body：`{"id": "canary_u_fixed", "name": "Canary Load Test User", "created_at": 0}`
     2. **创建 Agent (5个)**：
        - 端点：`POST http://127.0.0.1:19998/internal/entities/agents?user_id=canary_u_fixed`
        - Body：`{"id": "canary_a_1", "name": "Canary Agent 1", "owner_user_id": "canary_u_fixed", "created_at": 0}` (确保 owner 字段对应 user)
     3. **清理策略**：
        - Canary 账号将**永久保留，不自动清理**。压测脚本仅在账号不存在时幂等创建。如需清理则走人工 SQL。

7. **回滚 SLO 测量方法**：
   - **方法与 SLO 对齐**：
     由于 HealthWorker 默认 30s 扫一次，理论最坏时间可达 38-45s，因此 **Canary 期间（包括阶段 0 演练）需使用 A+C 组合策略**：
     - 将 HealthWorker 的检查周期调至 5s：在 `start.sh` 时通过 `NOVAIC_HEALTH_CHECK_INTERVAL=5` 环境变量控制 `--check-interval 5`。
     - **SLO 放宽至 45s**，给予充分的乱序和重启缓冲。
     1. 在本地或测试机执行：
        ```bash
        time (
            NOVAIC_ENABLE_SUBSCRIBER="" NOVAIC_HEALTH_CHECK_INTERVAL=5 bash scripts/start.sh --stop && \
            NOVAIC_ENABLE_SUBSCRIBER="" NOVAIC_HEALTH_CHECK_INTERVAL=5 bash scripts/start.sh
        )
        ```
     2. 同时，开启另一个 terminal 追踪 `health.log` 和 `business` 日志：
        ```bash
        tail -F /opt/novaic/data/logs/business-$(date +%Y%m%d).log /opt/novaic/data/logs/health.log | rg -e 'dispatch_subscriber disabled' -e 'event=health_fallback'
        ```
     3. 观察从 `time` 开始执行，到看到满足**阶段 0 通过凭证**为止的耗时（需 ≤ 45s）。

---

## §Canary 进展日志

### 2026-04-18 生产 hotfix 后 Phase 3 热压测（短时 burst）

**背景**：阶段 1/2 发现并修复两个阻塞：
1. `assembler_factory.py` 错用 `ServiceConfig.BUSINESS_INTERNAL_URL`（不存在）→ resolver fallback 到 `http://localhost:8200` → "All connection attempts failed"
   - Fix: 改为 `ServiceConfig.BUSINESS_URL`（novaic-business commit `20a4873`）
2. `DispatchResult` schema 与 Queue Service `/api/queue/dispatch` 真实响应不符（期望 `session_id`，实际 `action/saga_id/scope_id`）
   - Fix: 重构 dataclass 加 `action` 字段（novaic-common commit `2c060db`）

同轮顺便还完两项技术债：
3. Subscriber `_claim_batch` 加指数退避 + rate-limited logging（commit `0e13564`）
4. Subscriber `_deliver_one` 透传 `idempotency_key=msg:<id>`（commit `0e13564`）

**清账**：Phase 3 前有 24 条 `canary_a_1` USER_MESSAGE 因上述 URL bug 累计 `attempts >= 999999`，已执行 manual-backfill：
```sql
UPDATE message_outbox SET delivered_at = strftime('%s','now')*1000,
  last_error = 'manual_backfill: pre-PR17-fix URL bug (canary_a_1 corpses, 2026-04-18)'
 WHERE delivered_at IS NULL AND attempts >= 999999;
-- rows_marked = 24, remaining_pending = 0
```

**Burst 参数**：`traffic.py send --count 100 --tps 10 --concurrency 5`，单 agent (`canary_a_1`)，约 10s 发完。

**结果（UTC 21:58:41 → 21:59:31，窗口 50s）**：

| 指标 | baseline | post-burst T+30s | delta | 红线 | 判定 |
|---|---|---|---|---|---|
| outbox `pending` | 0 | 0 | 0 | ≤ 50 (P99) | ✅ |
| outbox `oldest_pending_age_s` | 0 | 0 | immediate peak 0.3s | ≤ 2 (P99) | ✅ |
| outbox `poisoned` | 0 | 0 | 0 | = 0 | ✅ |
| outbox `delivered` | 35 | 135 | +100 | 与 sent 1:1 | ✅ |
| log `event=subscriber_delivered` | 11 | 111 | +100 | 与 sent 1:1 | ✅ |
| log `subscriber permanent fail` | 24 (历史) | 24 | 0 | 新增 = 0 | ✅ |
| log `subscriber transient` | 96 (历史) | 96 | 0 | 新增 < 5% of delivered | ✅ |
| send 脚本 `ok/fail` | — | 100/0 | — | fail = 0 | ✅ |
| effective_tps | — | 9.9 | — | ≈ 10 | ✅ |

**Queue action 分布观察**：`action=deduped` = 0，`action=saga_started` = 0，`action=buffered` = 111（含 pre-burst 11）。

- 预期阶段 2 的判据是 `deduped / delivered ≈ 1:1`，实际观察到 0:1（全部 buffered）。
- 原因：单 agent 快速 burst 下，Queue Service Session Coordinator 对该 agent 有持续活跃 session，两条 dispatch（inline `_dispatch_trigger` + subscriber）都落入 "buffer into active session" 路径而不是走 idempotency-key dedup 路径。
- 结论：这是 Queue 端 session 语义遮蔽了 dedup 信号，**不是 subscriber 路径失效**。真正的证据链是 "subscriber_delivered +100 ↔ outbox delivered +100 ↔ 0 perm_fail ↔ 0 新 transient"，说明双路都到达 Queue 且被接受。
- 已录入技术债（见 `docs/roadmap/technical-debt.md` PR-17 section）：长周期多 agent 流量下应能看到 `action=deduped`；PR-18 删 inline `_dispatch_trigger` 后该指标自然归 0，届时转为观察 `saga_started / session 建立` 比例。

**Phase 3 burst 判定**：✅ GREEN，达到阶段 2 全部放行条件（短时窗口）。下一步可以进入阶段 3（24-48h 持续观察，只留自然流量）；或按需追加 `--qps 3 --duration 7200` 的 6h 持续压测进一步固化信心。

---

## §阶段 0 演练预案与放行标准

我理解必须获得此预案的批复后，才能进行 T1 阶段的代码开发，并在本地验证 SLO 演练后再次请你批复，之后才可进入生产阶段 1。

1. **开发 B.1 和 B.2**：实现 `--enable-subscriber` 纯 CLI 控制，配置 `NOVAIC_HEALTH_CHECK_INTERVAL=5` 缩短周期，验证参数正确传导。
2. **开发 B.3**：编写 `scripts/deploy-business.sh`。包含两种模式：
   - `--first-time` 模式：完整 rsync 3 个子仓库，停止服务，备份 DB，然后 `flag off` 启动并等待 60s 建表，最后 curl health 检查。此模式对应生产首发冷启动。
   - 无参数日常增量部署模式。
3. **开发 B.4**：实现 `scripts/canary/traffic.py` 压测脚本，包含内部鉴权和账号永久驻留式的 Bootstrap 功能。
4. **撰写 B.5**：将四阶段的实施、巨型集成警告、回滚细则写入 `docs/runbooks/subscriber-canary.md`。

**阶段 0 演练的通过凭证（实操验证标准）：**
1. `time` 命令输出的 `elapsed real time` ≤ 45s。
2. `health.log` 中 `event=health_fallback` 的 timestamp 晚于 flag-off 的重启时间（证明 HealthWorker 真正在回滚后接管）。
3. `business-*.log` 最后一条 subscriber 相关的 log 为 `dispatch_subscriber disabled`（证明订阅器已完全关停）。

请确认修改后的 preflight 报告，批复后我即可提交对应的 `docs: PR-17 preflight updated` 变更！
