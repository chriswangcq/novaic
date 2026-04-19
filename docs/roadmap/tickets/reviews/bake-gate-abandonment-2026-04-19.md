# 架构决策：撤销所有 bake gate（2026-04-19）

**状态**：已锁定
**范围**：PR-17 Phase 4 bake、PR-34 各 sub-PR 48h bake、PR-35 部署后观察期、`bake-snapshot.sh` cron job
**触发**：零流量生产环境下，bake 是信号噪声而不是信号源。

---

## §A 背景

"bake X 小时"这个词在我们过去几个 PR 里是什么意思？

- PR-17：Phase 1~4 共 77h 生产观察，cron 每 4h 跑 `scripts/canary/bake-snapshot.sh`，grep 日志 counter，按 §E 阈值判定放绿。
- PR-34：每个 sub-PR merge 后"单独 bake 48h"，gate 下一步。
- PR-35：双层防御部署后 prod smoke 一次 + 日志扫描。

这些 bake 设计假设一个事实：**生产有真实持续流量，足以在 X 小时内穿过代码的 race / peak / 边界路径**。

---

## §B 现状（2026-04-19）

- 生产 host `api.gradievo.com` **单人自用、零流量**：`grep -cE 'event=subscriber_delivered' business-*.log` 多日 = 0；`/opt/novaic/data/logs/business-$(date).log` 常常根本不存在（当日无日志产生）。
- `bake-snapshot.sh` 在这种环境下每 4h 产出的"WARN business_log=0"是**假信号**：它说的是"没日志"，不是"系统坏了"，但 ops 扫描会当成坏信号处理（本月已触发过 2 次误判）。
- 48h / 77h 观察期对零流量系统的**架构保障价值 ≈ 0**：没有流量就没有 race，没有 peak 就没有 leak 压力测试，没有边界 case 触发。唯一能测的"代码静态不 crash"一次 smoke 就够。

---

## §C 决策

**撤销所有 bake gate，改为两步最简验收**：

1. **部署前**：本地全量测试绿（各 submodule `pytest`、主仓 lint），**强制**。
2. **部署后**：一次 real smoke（人工发一条消息 → 看 agent 回复通 + tail 日志无 ERROR/Traceback）—— 约 30 秒。

**bake cron 立即停**：`crontab -e` 注释掉 `bake-snapshot.sh` 行，保留注释作为恢复参考。

---

## §D 实施动作（已完成）

- [x] `ssh root@api.gradievo.com "crontab -e"` — 注释掉 `0 */4 * * * .../bake-snapshot.sh ...`，前面加 `# DISABLED 2026-04-19 — zero-traffic prod ...`
- [x] `docs/roadmap/tickets/PR-34-worker-sync.md` — §D 表格"状态"列中 34b/34c/34d "等 bake 48h" → "等部署 + smoke"；§D.34b 的"生产观察 gate"节删除 / 改 smoke checklist
- [x] `docs/roadmap/tickets/PR-35-silent-fail-runtime-fill-defaults.md` — "部署观察期"相关段落标"撤销（见 bake-gate-abandonment-2026-04-19.md）"
- [x] `docs/roadmap/tickets/reviews/PR-17-preflight-guidance.md` — 顶部加 bake 撤销批注（不删正文，保留流量回来时恢复路径）
- [x] 当前未关闭的 PR（novaic-agent-runtime#2, Entangled#1, ...）body 的"bake 48h"段改为"smoke 1 请求即视为过"

---

## §E 何时恢复（回滚条件）

**任一条件达成即恢复 bake**：

- 日均 `subscriber_delivered` 计数 > 100（出现真实持续流量）
- 接入第二个真实用户（多租户压力出现）
- 部署任何 **涉及并发正确性假设** 的改动（locking、async/await 语义、跨进程 IPC）——这类改动单 smoke 不够

恢复步骤：

1. `ssh root@api.gradievo.com "crontab -e"`，把 `# DISABLED ...` 注释去掉 → cron 立即生效。
2. `bake-snapshot.sh` 脚本本身没删，已在 prod `/opt/novaic/services/scripts/canary/` 原位。
3. RFC 中"生产观察"节被删除的那些阈值表 → 从 git history 找回来，按当时的流量量级校准新阈值（旧的阈值是基于 10-100 qps 设计的，恢复时可能需重新校准）。

---

## §F 架构判断沉淀

- **"bake" 是一个假设持续流量的架构工具**，零流量场景下把它当仪式只会污染真实信号（违反"系统简单 + 无静默失败"原则，因为它主动制造伪 WARN）。
- **零流量 prod ≠ staging**：staging 的作用是冷启动正确性验证、pre-prod dev loop；真实零流量 prod 只是"部署管道本身是否工作"的 integration test。两者不该混淆。
- **观察期的本质是"等 state 穿过代码"**：没有 state 流动时观察 48h 和观察 0 秒等价，拉长窗口既不多一分保障也不少一分风险。
- 未来若要恢复 bake，不需要恢复**所有** bake gate，只需对当时真实触发的 PR 重建阈值。每次 RFC 应自问："该改动需要多少真实流量才能触发其失败模式？" 而不是默认抄前一个 RFC 的 48h。
