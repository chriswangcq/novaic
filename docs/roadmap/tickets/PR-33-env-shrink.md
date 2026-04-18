# PR-33 — Env 变量收窄（infra-track RFC）

**类型**：infrastructure refactor（与 message-wake 主线 PR-01~PR-32 正交）
**状态**：草稿（RFC），待老板审阅后进入 T1
**前置**：PR-17 Phase 4 bake 通过（不阻塞本 RFC 起草，但实施阶段必须等 bake 放绿）
**作者**：PR-17 Canary 收尾期的副产品
**读者**：junior / senior reviewer

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
    "scheduler_poll_interval_seconds": 1.0,
    "fallback_max_per_tick": 50
  }
}
```

- **读取方式**：`ServiceConfig.SUBSCRIBER_ENABLED`, `ServiceConfig.HEALTH_CHECK_INTERVAL_SECONDS`
- **热加载**：**不支持**，和其他 `services.json` 值一样，进程启动时读一次。需要切换 canary 就必须重启 Business / agent-runtime（反正我们一直这样做）。
- **dev/prod 差异**：
  - dev：committed `services.json` 默认关 (`subscriber_enabled: false`, `health_check_interval_seconds: 30`)
  - prod：在 `/opt/novaic/services/novaic-common/config/services.json` 本地编辑，或通过 `services.override.json`（gitignored, 若存在则 merge over）
  - 运维 runbook 的 "flip canary switch" 步骤：编辑 services.json → `bash start.sh --stop && bash start.sh`

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

### Phase 5 — 删 ownership.py / assembler_factory.py 的 env fallback

- `novaic-common/common/agents/ownership.py:97`: `business_url = os.getenv("BUSINESS_INTERNAL_URL", ...)` → 调用方必须显式传入 `business_url=ServiceConfig.BUSINESS_URL`。
- `novaic-agent-runtime/task_queue/workers/wake/assembler_factory.py:13-14`: `getattr(ServiceConfig, "BUSINESS_URL", os.environ.get(...))` → 去掉 `os.environ` 兜底，`ServiceConfig.BUSINESS_URL` 在 strict_config 里就是强校验必有字段，兜底永远不会触发。
- **测试**：跑 runtime / business / common 全 suite，确保无回归。

### Phase 6 — runbook + 文档

- 更新 `docs/runbooks/subscriber-canary.md`：翻 canary 开关的新流程（编辑 services.json → 重启），删掉所有 `export NOVAIC_ENABLE_SUBSCRIBER`。
- 更新 `docs/roadmap/technical-debt.md`：关闭"env 膨胀"条目（目前还没登记，PR-33 merge 时写进"已还清"）。
- 更新 `common/config.py` line 5 的 docstring：从 *"flows through the file or CLI args"* 改为 *"flows through services.json only"*（CLI args 至此基本清零）。

---

## §E 验收 metrics

| 指标 | 手段 | 期望 |
|---|---:|---|
| repo 内非法 env 读取数 | `rg "os\.(environ|getenv)" --type py` 减去允许白名单 | **0** 条新增；仅剩 §B 中标 ✅ 的 4 条 |
| `NOVAIC_*` 前缀在代码里剩余数 | `rg "NOVAIC_" --type py --type sh` | 仅 `NOVAIC_SERVICE_NAME` 保留 |
| health.log 中 `NOVAIC_INTERNAL_KEY is not set` 告警频率 | `grep -c` | **0**（Phase 4 后） |
| canary 开关端到端翻转耗时（edit config → restart → subscriber up） | 人工 + 日志时间戳 | ≤ 15 s（和今天一致） |

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

## §H 老板决策需要在 T1 前确认

- ✅ C.1 的"3 类 env 白名单"范围够不够宽？（`DEV_MODE` / `DEBUG` 这类"调试开关"要不要额外允许一类？我倾向不允许，用 services.json 的 `dev_mode` 即可）
- ✅ C.2 的"不做热 reload"是否接受？（我倾向接受，我们当前 2 个开关不需要）
- ✅ Phase 5 的 fallback 删除是否激进？（严格来说不删也没 bug，但留着就是死代码，倾向删）

审通过后进入 T1（代码实施），预估 1 人·周完成所有 6 个 Phase + 测试 + 运维 runbook。
