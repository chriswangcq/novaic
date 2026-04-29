# PR-33 — Env 变量收窄（infra-track RFC, v2）

**类型**：infrastructure refactor（与 message-wake 主线 PR-01~PR-32 正交）
**状态**：**v2 — 决策已锁定**（见 §H），等 PR-17 bake 放绿后启动 T1
**前置**：PR-17 Phase 4 bake 通过（不阻塞本 RFC 起草，但实施阶段必须等 bake 放绿）
**作者**：PR-17 Canary 收尾期的副产品
**读者**：junior / senior reviewer
**架构原则**（v2 基座，贯穿全篇决策）：
1. **系统简单** — 配置路径越少越好，类别越少越好，重启是唯一的切换手段。
2. **无静默失败** — 配置缺失必须在进程启动时 loud crash，永远不用 `default` 值掩盖缺失。

---

## §A 背景

`novaic-common/common/config.py` 第 5 行的承诺原文：

> *"No environment variables — all config flows through the file or CLI args."*

但经 2026-04-18 PR-17 Canary 收尾期的 repo 扫描，env 变量仍有 **7 处非法入口** + **2 处可疑 warning**，主要分布在 Canary 紧急路径、历史测试代码、以及 `common.http.clients` 里一条已归档（明确不做）功能的残留告警。

同期 `docs/roadmap/technical-debt.md` 的"内部 Key 未统一"条目被归档为 **✗ 明确不做**（PR-B 作废，见该文件 2026-04-18 复盘），所以 `NOVAIC_INTERNAL_KEY` 这条 env 入口**没有任何功能前景**，应该一并清理。

---

## §B 当前 env 使用盘点（repo grep 实测）

| # | 文件:行 | env 名 | 类别 | 处置 |
|---|---|---|---|---|
| 1 | `novaic-business/main_business.py:108` | `DISPATCH_SUBSCRIBER_ENABLED` | canary 开关 env fallback | ❌ 删，改走 services.json + CLI |
| 2 | `scripts/start.sh:46-52` | `NOVAIC_ENABLE_SUBSCRIBER` | canary 开关 env→CLI 桥 | ❌ 删，改走 services.json |
| 3 | `scripts/start.sh:46,47,208` | `NOVAIC_HEALTH_CHECK_INTERVAL` | health worker 周期 env override | ❌ 删，改走 services.json |
| 4 | `scripts/deploy-business.sh:211-213, 291-300` | 上述两个 env 的 `export` / `unset` | canary 工具脚本 | ❌ 跟随 2/3 一起删 |
| 5 | `novaic-common/common/http/clients.py:27,42` | `NOVAIC_INTERNAL_KEY` | 未实现功能的 WARNING | ❌ 整段删除（B 已归档为不做） |
| 6 | `novaic-common/common/agents/ownership.py:97` | `BUSINESS_INTERNAL_URL` | 测试用 fallback | ❌ 删，改用 `ServiceConfig.BUSINESS_URL` |
| 7 | `novaic-agent-runtime/task_queue/workers/wake/assembler_factory.py:13-14` | `BUSINESS_URL` / `QUEUE_SERVICE_URL` | ServiceConfig fallback | ❌ 删兜底 `os.environ.get`，ServiceConfig 是强校验的 |
| 8 | `novaic-common/common/auth.py:71` | `NOVAIC_SERVICE_NAME` | 服务自身身份 | ✅ **保留**，这是运行时 identity（不属于 config） |
| 9 | `novaic-agent-runtime/main_novaic.py:422-423` | `PATH`, `HOME` | OS 标准 env | ✅ **保留**（不是我们的 env） |
| 10 | `scripts/canary/traffic.py:62-63` | `CANARY_BUSINESS_URL`, `CANARY_ENTANGLED_DB` | 灰度测试工具 | ✅ **保留**（离线测试脚本，不进 prod） |
| 11 | `novaic-common/tests/test_internal_client.py:20-21` | `NOVAIC_INTERNAL_KEY` 的 `del` | 测试清理 | ✅ **保留**，但测试用例可能需要跟随 #5 删除 |

**净清理数**：7 处 env 入口 + 4 处 shell 导出/unset。

---

## §C 目标态（Post-PR-33）

### C.1 env 分类（唯一允许的 3 类）

| 类别 | 举例 | 存储 |
|---|---|---|
| 1. OS 标准 env | `PATH`, `HOME`, `USER`, `TMPDIR` | OS 提供 |
| 2. 部署模式 identity | `NOVAIC_SERVICE_NAME`（只读，由 start.sh 根据启动的具体 worker 设置） | start.sh 内联 export |
| 3. 离线测试工具 | `CANARY_*`（只在 `scripts/canary/` 下） | 开发者 shell |

**不再允许**：任何业务开关、URL、secret、超时/间隔数字通过 env 进入生产路径。

### C.2 运行时开关的新家（services.json）

```json
{
  "runtime_switches": {
    "subscriber_enabled": true,
    "health_check_interval_seconds": 30,
    "scheduler_poll_interval_seconds": 1.0
  }
}
```

- **读取方式**：`ServiceConfig.SUBSCRIBER_ENABLED`, `ServiceConfig.HEALTH_CHECK_INTERVAL_SECONDS`
- **热加载**：**不支持**，和其他 `services.json` 值一样，进程启动时读一次。需要切换 canary 就必须重启 Business / agent-runtime（反正我们一直这样做）。
- **dev/prod 差异**：
  - dev：committed `services.json` 默认关 (`subscriber_enabled: false`, `health_check_interval_seconds: 30`)
  - prod：overlay file `/opt/novaic/etc/runtime_switches.json`（见下 TD-5），deep-merge 覆盖 committed defaults
  - 运维 runbook 的 "flip canary switch" 步骤：编辑 **overlay file** → `bash start.sh --stop && bash start.sh`（不要编辑 services.json，rsync 会把你改的值冲掉）

### C.2.2 TD-5 — `runtime_switches` overlay（2026-04-15 根治）

**症状**：`deploy-business.sh` 每次跑 `rsync -azL --delete` 把 `novaic-common` / `novaic-gateway` / `novaic-agent-runtime` 三处 `services.json` 全覆盖，于是运维上一次开的 `subscriber_enabled=true` 会被悄悄改回 committed 的 `false`，subscriber 静默停摆。我们连着修了三次（每次手工 edit 三个 services.json + restart），问题总在下一次 deploy 复发。

**根因**：`runtime_switches` 和其他代码默认值住在同一个 rsync-owned 文件里，code-shipped defaults 和 ops-owned live config 之间没有物理隔离。

**根治**：overlay 机制。
- `services.json` 保留 `runtime_switches` 段做 **defaults**，rsync 照常覆盖。
- 新增 `/opt/novaic/etc/runtime_switches.json`，位置在 `$REMOTE_ROOT`（`/opt/novaic/services`）**之外**，rsync 物理碰不到。
- `common/strict_config.py` 的 `_apply_runtime_switches_overlay` 在 load 时把 overlay deep-merge 到 `runtime_switches` 上，overlay 赢。
- 查找顺序（先到先胜）：
  1. `NOVAIC_RUNTIME_SWITCHES_PATH` env var（测试专用）
  2. `$dirname(services.json)/runtime_switches.json`（dev 本地覆盖）
  3. `/opt/novaic/etc/runtime_switches.json`（prod canonical，所有服务进程共享一份）
- `deploy-business.sh` 的行为：
  - `RSYNC_EXCLUDES` 加 `--exclude 'runtime_switches.json'`（belt-and-braces：即便谁不小心在 rsynced tree 里放一份 sibling 也不会被 delete）
  - rsync 跑完后，若 `/opt/novaic/etc/runtime_switches.json` 不存在就用 committed defaults 种子化（**仅首次**），已存在则保留 operator-owned 内容。
- `start.sh` 的 `_cfg` helper 做同样的 overlay merge，保证 bash 端读到的 `subscriber_enabled` 和 Python 端完全一致。

**Fail-loud**：overlay 里出现 `services.json` 没声明过的 key（typo）→ ConfigError at startup。静默 no-op 是 TD-5 要消除的失败模式，不能在 overlay 里复活。

**测试**：`novaic-common/tests/test_strict_config_runtime_switches_overlay.py` — no-overlay-keeps-defaults / sibling-overlay-wins / nested-wrapper-accepted / unknown-key-crashes / env-override-wins / env-missing-file-crashes / non-dict-crashes。

### C.2.1 启动必须打印完整 runtime_switches 快照（强制，反静默失败）

每个 Python 进程（Gateway / Business / agent-runtime Worker / Queue Service / Cortex / File / Device）在 `main_*.py` lifespan 起始处必须打印一行 INFO 日志：

```
2026-04-19T03:00:00Z [INFO] ServiceConfig: runtime_switches={
  "subscriber_enabled": true,
  "health_check_interval_seconds": 5,
  "scheduler_poll_interval_seconds": 1.0
}
```

- 这是配置"生效状态"的**唯一可信快照**。运维判"这次重启有没有把 canary 开关打开"的唯一方法 = `grep "runtime_switches" business.log | head -1`。
- 实现放在 `ServiceConfig` 里加一个 `ServiceConfig.log_startup_snapshot(logger)` 类方法，每个服务 lifespan 头部调用。
- 禁止只打印部分字段或"本服务相关"字段——**全部 runtime_switches 打印**，因为一个字段在某服务不用也可能是被调用下游用到，需要审计。

### C.3 为什么不做"真正的热 reload"（Entangled config slot）

- 我们当前 2 个开关都是 **deploy-time**（canary 灰度、health 周期）。两者都自带了"restart 重启过程"作为切换手段。
- 真正的热 reload（Entangled config slot + watch）是 2-3 天工程，需要 slot schema 设计 / 前端管理面 / 审计日志。
- **本 PR 不做**。未来某个开关（比如实时速率限制）真需要热 reload 时再独立立项。

---

## §D 实施拆分

### Phase 1 — services.json schema 扩展（纯加，零风险）

- 给 `novaic-common/config/services.json` 加 `runtime_switches` 段，默认值与今天的 start.sh 默认值完全一致（`subscriber_enabled=false`, `health_check_interval_seconds=30`）。
- `novaic-common/common/config.py` 的 `ServiceConfig` 类添加 4 个常量（见 C.2）。
- `novaic-common/common/strict_config.py` 如果有 schema validation，补上这节的强校验。
- **测试**：`test_service_config_runtime_switches_defaults`、`test_service_config_runtime_switches_override_via_sidecar`

### Phase 2 — Business `--enable-subscriber` CLI 改为读 ServiceConfig

- `novaic-business/main_business.py`: 删掉 line 108 的 `_env_flag`，line 107 的 `_cli_flag` 也删。
- 新的 `SUBSCRIBER_ENABLED = ServiceConfig.SUBSCRIBER_ENABLED`。
- 删 `argparse.add_argument("--enable-subscriber", ...)` 以及 `--check-interval` 等相关 CLI 定义（如果存在）。
- **测试**：模拟 `services.override.json` 翻开关，重启后 `SUBSCRIBER_ENABLED == True`。

### Phase 3 — start.sh 删 env 桥

- 删 `scripts/start.sh:46-52, 208, 217` 里所有 `NOVAIC_ENABLE_SUBSCRIBER` / `NOVAIC_HEALTH_CHECK_INTERVAL` 逻辑。
- HealthWorker 启动参数 `--check-interval` 也删（worker 自己读 `ServiceConfig.HEALTH_CHECK_INTERVAL_SECONDS`）。
- `scripts/deploy-business.sh` 里 `unset NOVAIC_ENABLE_SUBSCRIBER`、`export NOVAIC_ENABLE_SUBSCRIBER=1` 对应段清理。
- **测试**：手工跑一遍 canary 翻开翻关流程（改 services.json + 重启），用 `grep -c "SUBSCRIBER_ENABLED=True"` 在启动日志里确认。

### Phase 4 — 清 clients.py 的 NOVAIC_INTERNAL_KEY warning

- `novaic-common/common/http/clients.py:27,42`：删掉两处 `if not os.environ.get("NOVAIC_INTERNAL_KEY"): logger.warning(...)`。
- `novaic-common/tests/test_internal_client.py:20-21`：相应测试清理代码删除（如果测试是为了确保 warning 不影响注入，那测试可以保留但移除 env 相关 setup）。
- **测试**：所有 common tests 继续绿。

### Phase 5 — 删 ownership.py / assembler_factory.py 的 env fallback（反静默失败关键步）

**为什么这条最重要**：PR-17 Canary 期间我们在 `assembler_factory.py` 就是因为这种 `getattr(ServiceConfig, "BUSINESS_INTERNAL_URL", os.environ.get(...))` 的三层 fallback，第一层字段名拼写错了静默落到第二层，第二层 env 没设静默落到 localhost，排查了两天才定位。这是**静默失败的教科书例子**。

- `novaic-common/common/agents/ownership.py:97`: `business_url = os.getenv("BUSINESS_INTERNAL_URL", ...)` → 调用方必须显式传入 `business_url=ServiceConfig.BUSINESS_URL`。
- `novaic-agent-runtime/task_queue/workers/wake/assembler_factory.py:13-14`: `getattr(ServiceConfig, "BUSINESS_URL", os.environ.get(...))` → 直接 `ServiceConfig.BUSINESS_URL`，缺字段就在 `ServiceConfig` 加载阶段 `AttributeError`——loud crash 正是期望行为。
- `common/strict_config.py` 在 `load_services_config()` 的 return 前做一次 schema 完整性校验：所有 `ServiceConfig` 引用的字段必须在 services.json 里存在（或有明确的 inline default）。
- **测试**：新增 `test_service_config_missing_key_raises` —— 删一个字段后，import 应抛异常而不是静默。
- **测试**：跑 runtime / business / common 全 suite，确保无回归。

### Phase 6 — runbook + 文档

- 更新 `docs/runbooks/subscriber-canary.md`：翻 canary 开关的新流程（编辑 services.json → 重启），删掉所有 `export NOVAIC_ENABLE_SUBSCRIBER`。
- 更新 `docs/roadmap/technical-debt.md`：关闭"env 膨胀"条目（目前还没登记，PR-33 merge 时写进"已还清"）。
- 更新 `common/config.py` 文件头 docstring：
  ```
  """Unified strict configuration facade.

  services.json is the SINGLE SOURCE OF TRUTH. Missing keys raise
  at startup (AttributeError / KeyError) — NEVER silently default.

  No environment variables except the three whitelist categories
  documented in docs/roadmap/tickets/PR-33-env-shrink.md §C.1:
    1. OS standard (PATH / HOME / USER / TMPDIR)
    2. Service identity (NOVAIC_SERVICE_NAME, set by start.sh)
    3. Offline test tools (CANARY_* under scripts/canary/ only)
  """
  ```

---

## §E 验收 metrics

| 指标 | 手段 | 期望 |
|---|---:|---|
| repo 内非法 env 读取数 | `rg "os\.(environ\|getenv)" --type py` 减去允许白名单 | **0** 条新增；仅剩 §B 中标 ✅ 的 4 条 |
| `NOVAIC_*` 前缀在代码里剩余数 | `rg "NOVAIC_" --type py --type sh` | 仅 `NOVAIC_SERVICE_NAME` 保留 |
| health.log 中 `NOVAIC_INTERNAL_KEY is not set` 告警频率 | `grep -c` | **0**（Phase 4 后） |
| canary 开关端到端翻转耗时（edit config → restart → subscriber up） | 人工 + 日志时间戳 | ≤ 15 s（和今天一致） |
| 启动日志必含 runtime_switches 快照 | `grep "runtime_switches=" business.log \| head -1` | **每次重启必有一条**，否则 CI 要检测到（见下） |
| 缺字段触发 loud crash | `pytest -k test_service_config_missing_key_raises` | ✅ 缺字段 → import 异常，不静默 default |

---

## §F 回滚路径

- Phase 1~6 内部任何一步失败：git revert 单个 commit，services.json 的 `runtime_switches` 段缺失时 strict_config 会 KeyError，提示清晰。
- **整 PR 失败**：revert merge commit，env 路径被 PR-17 时代的 deploy-business.sh 重新打开即可。不碰 secrets / URLs，零数据风险。

---

## §G 不在本 PR 做的事（严格排除）

- ❌ Entangled config slot / 热 reload 机制（see §C.3）
- ❌ 统一 `NOVAIC_INTERNAL_KEY`（已归档为不做，see technical-debt.md）
- ❌ `NOVAIC_SERVICE_NAME` 的 identity 重构（真 OS-level env，合理保留）
- ❌ secrets 挪出 services.json（secrets 已经在 services.json 的 secrets 段，**本就不是 env**，不需要动）
- ❌ worker 同步化（见 PR-34 RFC）

---

## §H 决策（v2，已锁定）

按"系统简单 + 无静默失败"双尺衡量后的最终裁决：

| 决策点 | 结论 | 理由（简单 / 静默失败两轴） |
|---|---|---|
| C.1 env 白名单只保留 3 类 | ✅ **锁定** | 简单：类别越少越好，加第 4 类即是滑坡起点。静默：`os.environ.get("DEBUG")` 忘 set 就静默失效，改用 `ServiceConfig.DEV_MODE` + 标准 logging level |
| C.2 不做热 reload | ✅ **锁定并强化** | 简单：watcher + partial-state semantics 是巨量复杂性。静默：watcher 挂了没人知道、reload 半新半旧状态都是经典静默失败。**强化**：每次进程启动强制打印完整 runtime_switches 快照（§C.2.1） |
| Phase 5 删 fallback | ✅ **锁定** | 这正是反静默失败的关键步；PR-17 的 `BUSINESS_INTERNAL_URL` 两天 debug 事故就是这种 fallback 导致的。改为缺字段 loud crash |

**T1 启动前提**：PR-17 Phase 4 bake 放绿（约 2026-04-19 22:40 UTC 满 24h）。

预估 1 人·周完成 6 个 Phase + 测试 + 运维 runbook + startup snapshot 接入。
