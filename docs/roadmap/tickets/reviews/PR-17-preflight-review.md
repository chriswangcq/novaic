# PR-17 Preflight Review

**结论**：**条件批准**——discovery 扎实，但小弟低估了一个重大发现。T1 开始前必须把 3 件事定死、1 件事告知老板。

---

## ✅ 做得好的地方

- 生产 `/opt/novaic/services/novaic-business` 不是 git repo + 无 `subscribers/` 目录 → 正确推断"版本早于 PR-15"
- `message_outbox` 表不存在 → 正确推断"Entangled 也早于 PR-14"
- 日志 ASCII 化确认，bootstrap 账号策略方向正确
- 7 个 discovery 问题一个不漏

---

## ⚠️ 被低估的重大发现（必须告诉老板）

### 发现：生产代码版本是 "pre-PR-15"

这不是"开个 subscriber flag 的小 Canary"，**这是一次从 PR-04 到 PR-16 的巨型集成上线**。

下面这些 PR 的生产代码**都是第一次上生产**：

| PR | 变更 | 首次在生产生效 |
|---|---|---|
| PR-05 | `internal_client` 强制 `service_name` | ✔️ 第一次 |
| PR-06 | `CallerLoggingMiddleware` 统一日志 | ✔️ 第一次 |
| PR-07 | `/internal/agents/{id}/owner` 端点 | ✔️ 第一次 |
| PR-08 | `AgentOwnershipResolver` 带 TTL 缓存 | ✔️ 第一次 |
| PR-09 | `TriggerType` 权威枚举解析旧数据 | ✔️ 第一次（**数据兼容风险**） |
| PR-10~13 | `DispatchAssembler` 替代老 `SagaClient.dispatch` | ✔️ 第一次 |
| PR-14 | `message_outbox` 表 + co-transaction INSERT | ✔️ 第一次（**schema migration**） |
| PR-15/16 | Subscriber 骨架 + 全量实现 | ✔️ 第一次 |

**含义**：Canary 阶段 1 的任何异常都可能来自以上任一 PR 的回归 bug，**不只是 subscriber 本身**。红线阈值要更保守，观察期要更耐心，回滚要更果断。

**行动**：
1. 在 `docs/runbooks/subscriber-canary.md` 开头加**"风险警示"章节**，列出上表
2. 阶段 1 观察期从 "2h" **延长到 "4-6h"**（给 Caller middleware / Ownership resolver / TriggerType migration 更多采样时间）
3. 阶段 1 新增监控项：
   - `rg 'ERROR|Exception|Traceback' business-*.log` 全窗口应 = 0（不只是 subscriber 相关的）
   - `rg 'agent_owner_lookup.*result=miss' business-*.log` 应 = 0（AgentOwnershipResolver 不应该在真实流量里出现 miss，除非数据本身就有问题）
   - `rg 'caller=unknown' business-*.log` 应 = 0（如出现说明 InternalCallerMiddleware 有漏口）
4. 阶段 1 前增加一个 **"冷启动确认"** 步骤：
   - `ssh` 上去 `ps aux | grep main_` 看 7 个进程全起（entangled/gateway/business/device/queue/file/cortex + workers）
   - 每个进程的启动日志有无 Traceback
   - `curl localhost:19998/health` 应 200

---

## 🔴 Blocker：3 件事 T1 前必须定死

### B.1 Bootstrap 账号方案还是 handwave 状态

第 6 点"通过脚本使用 novaic-common 中的 Entity/Internal API"——**具体是哪个 API？** 没写。这又是"方向对 + 细节 handwave"复发。

T1 前必须回答：

```markdown
## Bootstrap 具体步骤

1. 创建 User:
   - 端点：POST http://127.0.0.1:19998/internal/entities/users/action/create
     （或你 discovery 发现的真实路径）
   - JWT：需明确用 services.json 的 jwt_secret 签发一个 service token
     或复用 `X-Internal-Key: $JWT_SECRET` + `X-Internal-Service: canary-traffic`
   - Body: { "user_id": "canary_u_fixed", "username": "canary_fixed", ... }
   - 关键字段：<列出 User entity 的必填字段>

2. 创建 5 个 Agent:
   - 端点：...
   - Body: { "agent_id": "canary_a_1", "user_id": "canary_u_fixed", ... }
   - 关键字段：必须有 owner_user_id 或 user_id 指向 canary_u_fixed
     （否则 PR-07 `/owner` 端点会 404 → subscriber permanent fail kind=no_owner）

3. 幂等性：bootstrap 脚本必须幂等（已存在则跳过），避免压测多次启动时重复创建
```

**你必须在 preflight 里完成这段**——实地查 business 的 entity create API，而不是猜。不查清楚 T1 会卡死。

### B.2 30s 回滚 SLO 与 HealthWorker 30s 检查周期冲突

`scripts/start.sh` line 192：

```bash
$PY $MAIN health $WORKER_ARGS --check-interval 30 ...
```

**HealthWorker 默认 30s 才扫一次未读消息**。从"关 flag → restart → 第一条 fallback dispatch"的最坏情况：

```
0s    关 flag 请求发出
2s    start.sh --stop 完成
8s    start.sh 重启各服务完成
8s    HealthWorker 刚好错过了上一个 tick
38s   HealthWorker 下一次 tick（此时才 pick up fallback message）
```

**理论最坏 38-45s**，30s SLO 数学上不成立。

**决策**（T1 前定死）：
- 方案 A：**Canary 期间 start.sh 把 `--check-interval` 调到 5s**（用 shell 变量控制，默认 30s，Canary 时 export 为 5s）
- 方案 B：SLO 放宽到 60s
- 方案 C：既调 5s 也放宽 SLO 到 45s

我建议 **A + C 组合**：Canary 期间用 5s 检查周期，SLO 定 45s（留 15s buffer 给各种乱序）。

preflight 里选一个、写进 runbook。

### B.3 `deploy-business.sh` 的"首次上线"vs"日常更新"区分

生产目前是 pre-PR-15，所以 PR-17 的**第一次部署 = 大升级**。脚本要支持两种模式：

```bash
scripts/deploy-business.sh --first-time   # rsync 全部 + 初始化 schema + 重启
scripts/deploy-business.sh                  # 日常增量 rsync + 重启
```

`--first-time` 模式额外做：
1. 停所有服务：`ssh ... "bash /opt/novaic/services/scripts/start.sh --stop"`
2. 备份 entangled.db：`ssh ... "cp /opt/novaic/data/entangled.db /opt/novaic/data/entangled.db.bak-$(date +%s)"`
3. rsync 3 个子仓库（novaic-business、Entangled、novaic-common）
4. 起服务（subscriber flag 保持 off）
5. 等 60s 让 `ensure_schema` 跑完，再 `sqlite3 ... '.schema message_outbox'` 确认建表
6. `curl localhost:19998/health` / `curl localhost:19900/health` 健康检查

**首次上线至少分 2 步**：
- Step A：部署新代码，**flag off**，观察 30 min 冷启动（这一步纯粹是验证 PR-04~16 的代码本身能在生产跑起来，还没开 subscriber）
- Step B：冷启动稳定后，再开 flag 进阶段 1

这点要求在 runbook 里明确拆出来。

---

## 📝 次要修正

### M.1 健康日志路径写错了

你写的：
```bash
tail -F /opt/novaic/data/logs/runtime/health-worker-$(date +%Y%m%d).log
```

实际是（`start.sh` line 192）：
```bash
tail -F /opt/novaic/data/logs/health.log
```

单文件、不切日。SLO 测量命令里改一下。

### M.2 阶段 0 演练的"通过凭证"写模糊

你写 "在本地验证 SLO 后再找你批复"——**具体拿什么给我看？**

明确为：
```markdown
阶段 0 通过凭证（preflight 报告回写时贴）：
1. `time` 命令输出的 elapsed real time ≤ 45s
2. health.log 里 `event=health_fallback` 出现在 flag-off 后的 timestamp（证明 HealthWorker 真的接管了）
3. business-*.log 最后一条 subscriber log 是 "dispatch_subscriber disabled"（证明 subscriber 真的关了）
3 条全具备才算阶段 0 通过。
```

### M.3 Bootstrap 的清理选项

第 6 点提到"压测结束后提供清理选项或保留以供后续使用"——**默认应该保留**。理由：
- 压测账号本身没有隐私/合规问题（都是 canary_* 前缀）
- 下次 Canary 或者 PR-18/19 还要复用
- 清理万一误删真用户后果严重

runbook 里明确："canary 账号永久保留，不自动清理；如需清理走人工 SQL"。

---

## 🎯 T1 放行标准

你满足下面全部才能进 T1：

- [ ] 在 preflight 报告追加 "重大发现：生产 pre-PR-15 → Canary 是巨型集成上线" 章节，列出受影响的 PR 列表
- [ ] Bootstrap 技术细节（B.1）写死到 preflight
- [ ] HealthWorker check-interval + SLO 方案（B.2）选定
- [ ] `deploy-business.sh` 的 `--first-time` 拆分策略（B.3）写清楚
- [ ] 健康日志路径（M.1）改对
- [ ] 阶段 0 通过凭证（M.2）明确

追加完后再 commit 一版 preflight，commit message：

```
docs: PR-17 preflight updated per review (pre-PR-15 implication, bootstrap details, SLO alignment)
```

**不要在 preflight 里开写 T1 代码**——等我再审一轮批复，才进开发。

---

## 📋 T1 阶段分步（批复后你照这个来）

T1 阶段 commit 结构（6 段）在 `docs/roadmap/tickets/reviews/PR-17-preflight-guidance.md` §G 已列清。严格按那个拆。

阶段 0 演练在**你本机**做，不在生产做。验证通过后回来让我批复才动生产。

阶段 1-3 每次状态转换都要**回到这个 review 文件找我**——不自作主张往下推。生产 Canary 是最慢但最保险的节奏。

