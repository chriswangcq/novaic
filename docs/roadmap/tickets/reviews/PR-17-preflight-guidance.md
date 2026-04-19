# PR-17 Preflight 指引（Canary 上生产）

**读者**：junior
**写者**：senior reviewer
**状态**：此文件是**任务导航**，不是 preflight 报告本身。你读完后需要写 `docs/roadmap/tickets/reviews/PR-17-preflight-antigravity.md` 回答 §F 的 discovery 问题 + 确认实施方案，拿到批复后才进入 T1。

> **2026-04-19 UPDATE — Canary bake gate 已撤销**
> 零流量生产环境下 4 阶段 77h bake 是伪仪式，见
> `[bake-gate-abandonment-2026-04-19.md](./bake-gate-abandonment-2026-04-19.md)`。
> PR-17 本身视为已完成，直接进入 merge / deploy，部署后跑一次人工 smoke
> （发一条消息 → agent 回复通 + 日志无 Traceback）即放行。
> §E 指标表和 Phase 1~4 节保留作为**流量回来时恢复 bake 的参考模板**，不再是当前验收口径。

---

## §A 生产部署架构（先读明白，别瞎猜）


| 事实               | 值                                                                                                                            |
| ---------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| 生产 host          | `root@api.gradievo.com`（Gateway `deploy-gateway.sh` 同目标）                                                                     |
| 代码路径             | `/opt/novaic/services/<submodule>/`                                                                                          |
| 启动脚本             | `/opt/novaic/services/scripts/start.sh` ← 这个 repo 里的 `scripts/start.sh`                                                      |
| Business 启动行     | `start.sh` line 131-135，`python main_business.py --host ... --port ... --data-dir ... --entangled-url ... --gateway-url ...` |
| Business 日志      | `/opt/novaic/data/logs/business-YYYYMMDD.log`（UTC 按日切）                                                                       |
| Entangled DB 路径  | `/opt/novaic/data/entangled.db`（SQLite，可 `sqlite3` 直查）                                                                       |
| 部署 Business 的脚本  | **不存在**（只有 `scripts/gateway/deploy-gateway.sh` 部署 Gateway）——你得写                                                              |
| 配置风格             | **Zero exports，纯 CLI args**（`start.sh` line 7 有明确声明）                                                                         |
| 当前 subscriber 状态 | **从未开过**（`start.sh` 里既没 `DISPATCH_SUBSCRIBER_ENABLED=1` export 也没 `--enable-subscriber` arg）                                 |


---

## §B PR-17 T1 范围（严格收窄）

只做这 5 件事，不许扩：

### B.1 把 `SUBSCRIBER_ENABLED` 从 env 改成 CLI arg

- `novaic-business/main_business.py`：
  - 在现有 argparse 里加 `--enable-subscriber` flag（`action="store_true"`，默认 False）
  - 把 line 100 `SUBSCRIBER_ENABLED = os.environ.get("DISPATCH_SUBSCRIBER_ENABLED", "0") == "1"` 改为从 `_cli_args.enable_subscriber` 读
  - **保留对 env 的 fallback 读取**（防本地开发习惯破坏）：`SUBSCRIBER_ENABLED = _cli_args.enable_subscriber or os.environ.get("DISPATCH_SUBSCRIBER_ENABLED", "0") == "1"`
- 理由：遵循 `start.sh` 的 "Zero exports" 原则（line 7 明确声明），让 `ps aux` 能直接看到 flag 状态

### B.2 `scripts/start.sh` Business 启动行加开关

line 131-134 的启动命令追加 `--enable-subscriber`，但**默认注释掉**，用 shell 变量控制：

```bash
# 在 Ports 区域附近新增
SUBSCRIBER_FLAG="${NOVAIC_ENABLE_SUBSCRIBER:-}"   # 设为 --enable-subscriber 时开启

# Business 启动行改为
$(py novaic-gateway) "$BASE/novaic-business/main_business.py" \
    --host "$HOST" --port "$PORT_BUSINESS" --data-dir "$DATA_DIR" \
    --entangled-url "$ENTANGLED_URL" --gateway-url "$GW_URL" \
    $SUBSCRIBER_FLAG \
    >> "$LOG_DIR/business-$(date +%Y%m%d).log" 2>&1 &
```

生产开 Canary 就 `NOVAIC_ENABLE_SUBSCRIBER="--enable-subscriber" bash scripts/start.sh`，关 Canary 就不带这个 env（或显式 `NOVAIC_ENABLE_SUBSCRIBER=""`）重启。

### B.3 写 `scripts/deploy-business.sh`

仿 `scripts/gateway/deploy-gateway.sh` 结构，rsync `novaic-business/`、`Entangled/`、`novaic-common/` 三个子仓库到生产（Subscriber 依赖这三个），然后 `bash scripts/start.sh --stop && bash scripts/start.sh`。

**关键 discovery**：看一下 `deploy-gateway.sh` 是不是也 rsync 了 `novaic-common` / `Entangled`。如果是，那 PR-14/15/16 的代码早已被 gateway 部署带上去了——意味着生产 message_outbox 表可能已存在并积压。这个你必须在 §F discovery 里核实清楚。

### B.4 写 `scripts/canary/traffic.py` 压测脚本

- 目标端点：`POST http://127.0.0.1:19998/internal/entities/messages/action/send`
- 负载：随机生成 `user_id`、`agent_id` / SUBAGENT_SEND 和 SPAWN_SUBAGENT 也各占一定比例
- 默认 1 QPS，接受 `--qps N --duration S` 参数
- 加 `--target <url>` 支持指向本地 or 生产
- **一定要带 X-Internal-Key**（生产 business 有 CallerLoggingMiddleware，未鉴权请求会被拒）
- 输出：每秒打印 sent/acked/error 计数
- **严禁**写真实用户 ID——要用形如 `canary_u_`* / `canary_a_*` 的明显前缀，方便事后从生产 entangled.db 一键清理

压测前必须先在 Business 加一个 env/CLI flag `--allow-canary-user-prefix=canary_`，让 CallerLoggingMiddleware 或者 send_action 识别到 canary 前缀时走隔离路径（如 agent/user 不存在就返回 200 而不是 404）。**别直接往生产真数据表里灌垃圾**。

实际上更简单的做法：**压测脚本先 create 一个固定的 `canary_u_fixed` 用户 + 5 个 `canary_a_`* agent，然后只对这几个账号发 message**。这样既真实走完整链路（走 ownership lookup / outbox insert / subscriber 消费），又不污染真实用户。

### B.5 `docs/runbooks/subscriber-canary.md`

按 §C 的四阶段模板全写进去，含每阶段的命令行、判定阈值、回滚步骤、异常处理决策树。

---

## §C 四阶段 Canary 实施手册

### 阶段 0：Discovery & 回滚演练（老板批准后才能进阶段 1）

在**本地**先演练一次 flag on/off 切换，验证：

1. `NOVAIC_ENABLE_SUBSCRIBER="--enable-subscriber" bash scripts/start.sh` 启动后，business 日志有 `dispatch_subscriber enabled worker_id=...`
2. 发 3 条 USER_MESSAGE → 看 outbox 表 `SELECT * FROM message_outbox WHERE delivered_at IS NOT NULL`，应有对应行且 `delivered_at` 填了
3. **触发回滚**：`bash scripts/start.sh --stop` 然后 `bash scripts/start.sh`（不带 env），business 日志应打 `dispatch_subscriber disabled`
4. **关键 SLO**：从 "`--stop`" 执行到 "`start.sh` 返回 + HealthWorker 接管第一条 fallback message" ≤ 30s（用 `time` 包住 + log 对照）

演练结束贴数据到 preflight 报告。

### 阶段 1：生产静态冷启动（2h 自然流量）

```bash
# 生产 host 上
export NOVAIC_ENABLE_SUBSCRIBER="--enable-subscriber"
bash /opt/novaic/services/scripts/start.sh --stop
bash /opt/novaic/services/scripts/start.sh

# 本地起一个持续观察循环
while true; do
  echo "=== $(date) ==="
  ssh root@api.gradievo.com "sqlite3 /opt/novaic/data/entangled.db '
    SELECT COUNT(*) as pending FROM message_outbox WHERE delivered_at IS NULL;
    SELECT MAX((strftime(\"%s\",\"now\")*1000 - created_at)/1000) as oldest_age_s FROM message_outbox WHERE delivered_at IS NULL;
  '"
  ssh root@api.gradievo.com "rg -c 'event=subscriber_delivered' /opt/novaic/data/logs/business-$(date +%Y%m%d).log || echo 0"
  ssh root@api.gradievo.com "rg -c 'subscriber permanent fail' /opt/novaic/data/logs/business-$(date +%Y%m%d).log || echo 0"
  sleep 30
done
```

**继续条件（全部满足才进阶段 2）**：

- `pending` ≤ 10（偶有排队正常，持续积累不行）
- `oldest_age_s` 任何时刻 ≤ 5
- `subscriber permanent fail` 计数 = 0
- `rg 'action=deduped' business-*.log` 出现频次 > 0（证明双发安全网在工作，因为 `_dispatch_trigger` 仍在写）

**触发红线立即回滚**：任一条件破（持续超过 1 min 不回弹）→ 去 `NOVAIC_ENABLE_SUBSCRIBER` env → restart → 回到 flag off。

### 阶段 2：热压测（2-4h，压测脚本 + 自然流量）

```bash
# 本地起压测
python scripts/canary/traffic.py --target https://api.gradievo.com --qps 3 --duration 7200
```

**继续条件**：

- outbox `pending` P99 ≤ 50，P50 ≤ 5
- `oldest_age_s` P99 ≤ 2
- `subscriber transient` / `subscriber_delivered` 比例 < 5%
- 压测期间真实用户（非 canary 前缀）的消息处理正常（人肉在另一个设备发几条真实 hihi 对话验证）

**红线**：

- `pending` 持续 > 200 → 回滚
- `oldest_age_s` > 10s → 回滚
- 任一 `subscriber permanent fail kind=no_owner` → 回滚（数据一致性问题）

### 阶段 3：持续观察（24-48h，压测停，只留自然流量）

- 每 4h 自动跑一次 §C 阶段 1 的监控循环，抓 snapshot 写日记
- 观察 `action=deduped` 比例稳定性——这代表 "subscriber + inline dispatch 双发去重"一直在正常工作
- `subscriber permanent fail` 整窗口 = 0

**窗口内任何时刻回滚**：回到 flag off → 留 1h 稳定 → 人工 root cause → 决定是否需要代码修复

---

## §D 回滚 playbook（必须背到滚瓜烂熟）

```bash
# 最快路径（30s SLO）
ssh root@api.gradievo.com << 'EOF'
unset NOVAIC_ENABLE_SUBSCRIBER
bash /opt/novaic/services/scripts/start.sh --stop
bash /opt/novaic/services/scripts/start.sh
tail -5 /opt/novaic/data/logs/business-$(date +%Y%m%d).log
EOF
# 期望输出包含 "dispatch_subscriber disabled"
```

**关 flag 后 outbox 的长期副作用**：

- `message_outbox` 表的 insert 是 Entangled 侧无条件的（PR-14 的 co-transaction），不受 Business flag 控制
- 关了 subscriber，outbox 行会无人消费 → 无限堆积
- `scripts/outbox-compact.sh` 只清理 `delivered_at IS NOT NULL` 的行，**对未消费行无能为力**
- **短期回滚（< 数日）可接受**，长期关闭必须在 runbook 单独加一节手动清理命令：
  ```sql
  UPDATE message_outbox SET delivered_at = strftime('%s','now')*1000, last_error = 'manual_backfill: subscriber disabled long term'
   WHERE delivered_at IS NULL AND created_at < strftime('%s','now','-1 day')*1000;
  ```

把这点**明确写进 runbook**。

---

## §E log+SQL 替代 metric 表

因为 PR-32 的 Prometheus metric 要等到 Phase 2 后再做，Canary 的全部判定工具就是下面这张表。**背熟**。


| 原 metric                                 | 替代查询                                                                                                         | 红线阈值                                                                      |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------- |
| `subscriber_delivered_total`             | `rg -c 'event=subscriber_delivered' business-*.log`                                                          | 单调增（不增 = 消费停了）                                                            |
| `subscriber_failed_total{kind=no_owner}` | `rg -c 'subscriber permanent fail.*kind=no_owner' business-*.log`                                            | = 0                                                                       |
| `subscriber_failed_total{kind=other}`    | `rg -c 'subscriber permanent fail' - 上一行 grep`                                                               | < `subscriber_delivered` 的 0.1%                                           |
| `subscriber_retry_total`                 | `rg -c 'subscriber transient' business-*.log`                                                                | < `subscriber_delivered` 的 5%                                             |
| `outbox_lag_seconds`                     | `SELECT MAX((strftime('%s','now')*1000 - created_at)/1000.0) FROM message_outbox WHERE delivered_at IS NULL` | P99 ≤ 2s                                                                  |
| `outbox_backlog_count`                   | `SELECT COUNT(*) FROM message_outbox WHERE delivered_at IS NULL`                                             | 持续 < 50                                                                   |
| `action=deduped` 比例                      | `rg -c 'action=deduped' / rg -c 'event=subscriber_delivered'`                                                | 阶段 1/2 应接近 1:1（因为 inline dispatch 先到），Canary 通过后 PR-18 删 inline 这个比例才会归 0 |
| `healthworker_scan_total` 真 re-dispatch  | `rg -c 'event=health_fallback' runtime/health-worker-*.log`                                                  | 应从 PR-12 的水平 → 接近 0（因为 subscriber 接管）                                     |


---

## §F Preflight 报告必须回答的 Discovery 问题

把下面每一条的答案**真实查出来**贴到 `docs/roadmap/tickets/reviews/PR-17-preflight-antigravity.md`。**不许猜，要 ssh 到生产实地查**：

1. **生产当前 Business 代码版本**：`ssh root@api.gradievo.com "cd /opt/novaic/services/novaic-business && git log -1 --oneline"`——是 PR-16 之后吗？如果早于 PR-14，先回答"PR-17 必须先做一次完整的三子仓库（Entangled/novaic-common/novaic-business）同步部署"
2. **生产 message_outbox 表是否存在**：`ssh root@api.gradievo.com "sqlite3 /opt/novaic/data/entangled.db '.schema message_outbox'"`——如果表不存在，意味着 Entangled 侧的 `ensure_schema` 没跑过 PR-14 的 outbox 分支，要先 rsync 新 Entangled + 重启
3. **当前 outbox 积压量**（如果表存在）：`SELECT COUNT(*) FROM message_outbox WHERE delivered_at IS NULL` 应该很小，如果已经堆积几百条说明 PR-14 已在生产跑了但没人消费，**这是个更紧急的现状**
4. **生产 Business 日志的格式**：`ssh root@api.gradievo.com "head -20 /opt/novaic/data/logs/business-$(date +%Y%m%d).log"`——确认日志能被 `rg` 解析（有 ASCII 文本，不是二进制/压缩过的）
5. `**deploy-gateway.sh` 是否已经带上了 novaic-common / Entangled**：读一遍代码，看 rsync 的源目录清单。如果只有 `novaic-gateway/`，那生产的 novaic-common / Entangled 肯定不是最新版——回答"deploy-business.sh 需要 rsync 三个子仓库"。
6. **压测脚本的隔离账号策略**：确认生产有没有现成的 `canary_`* 测试账号？没有的话，你的 canary traffic 第一步要先 bootstrap 这些账号。preflight 里列出 bootstrap SQL/API。
7. **回滚 SLO 测量方法**：本地阶段 0 演练时怎么测 "30s 内 HealthWorker 接管第一条 fallback"？具体 tail 哪个日志、看什么字段？

---

## §G 交付格式 + Commit 拆分

**5 段 commit（2 子模块 + 3 主仓 docs/scripts）**：


| #   | 子模块               | Message                                                                  |
| --- | ----------------- | ------------------------------------------------------------------------ |
| 1   | `novaic-business` | `feat(business): add --enable-subscriber CLI arg (PR-17)`                |
| 2   | 主仓 scripts        | `feat(scripts): start.sh supports NOVAIC_ENABLE_SUBSCRIBER flag (PR-17)` |
| 3   | 主仓 scripts        | `feat(scripts): add deploy-business.sh (PR-17)`                          |
| 4   | 主仓 scripts        | `feat(scripts): add canary traffic.py for PR-17 observation`             |
| 5   | 主仓 docs           | `docs: subscriber-canary runbook + PR-17 ticket check-off (partial)`     |
| 6   | 主仓                | `chore: bump submodules for PR-17`（独立拎出来，**不要又绑 docs**）                  |


**Declare Done 前三问自检**（PR-16 的教训）：

1. 每个勾对应一段可执行凭证吗？
2. 每个 commit 能独立 revert 吗？
3. 去掉生产代码，测试会不会红？

**观察期 Status**：`[-] observation_pending`，**不允许** `[x]`。阶段 3 结束、数据干净，才允许 `[x]`。

---

## §H 不在本 PR 做的事（严格排除）

- ❌ 动 metric 代码（等 PR-32）
- ❌ 删 `_dispatch_trigger`（等 PR-18）
- ❌ 改 HealthWorker（等 PR-19）
- ❌ 改 message_outbox schema（等 PR-26 要动时再说）
- ❌ 加自适应 poll_interval（PR-16 被否过）
- ❌ 让压测走真实用户账号

---

## 老板决策需要在 preflight 里承诺

- ✅ 四阶段 Canary 接受（已批）
- ✅ 生产部署（已批）
- ✅ 压测脚本（已批）
- ⏳ 阶段 0 演练完成后**需回到此文件找我重新审批**才能进阶段 1。阶段 0 演练结果用 preflight 报告 §阶段0 的 subsection 回贴给我。

