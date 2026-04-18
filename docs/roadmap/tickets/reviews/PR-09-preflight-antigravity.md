# PR-09: TriggerType 权威枚举 + schema 迁移调研报告

## 1. File:Line 表 (跨语言搜索 `user_response` 的清点)

通过对全仓跨语言（TS / Rust / JSON / Python）搜索 `"user_response"`，确认存在以下由于枚举漂移导致必须修改的落点，它们都需要被统一替换为 `user_message`：

| 文件路径 | 行号 | 出现上下文与修改动作 |
| --- | --- | --- |
| `novaic-common/common/tools/definitions.py` | L512, L522 | JSON Schema 中 agent wake_triggers 的 default 描述。**注意**：L512 枚举里有 `["user_response", "timer", "event"]`，本 PR **仅**替换 `user_response` 为 `user_message`，保留 `timer / event` 不动。 |
| `novaic-business/business/internal/subagent_utils.py` | L249 | 创建 subagent 时代码里硬编码的 `[{"type": "user_response"}]`，替换为 `TriggerType.USER_MESSAGE.value`。 |
| `novaic-business/business/schema_push.py` | L110 | Entangled Schema 定义中默认值的硬编码，改为 `[{"type":"user_message"}]`。 |
| `novaic-business/business/internal/subagent.py` | L296 | 解析 payload 中如果缺少 `wake_triggers` 时的 fallback，改为 `TriggerType.USER_MESSAGE.value`。 |
| `scripts/migrations/2026-XX-XX-wake-triggers-rename.sql` | 新增 | 执行全量 SQLite 的 `REPLACE`。 |

> **注**：经查 `novaic-app`（TS/前端）和 Rust 端均无对 `"user_response"` 的硬编码，前端的常量为 `USER_MESSAGE`（表示消息类型），无需额外修复。

## 2. 测试 Checklist

### 枚举及应用单测
- [x] 单测：`TriggerType.from_legacy("user_response") is TriggerType.USER_MESSAGE`
- [x] 端到端：新建 subagent，断言 `wake_triggers` 默认保存的确实是 `[{"type": "user_message"}]`。

### 【重要】生产数据迁移幂等测试
- [x] **先决取样**：在拷贝 DB 上 sample 5-10 条真实 `wake_triggers`，确认 JSON 字符串是否严格带双引号。如混杂单/无引号格式，则补一版单引号的 `REPLACE` 兼容。
- [x] **拷贝 DB**：复制线上的 `entangled.db` 为拷贝副本。
- [x] **首次执行**：运行 `UPDATE ... WHERE ... LIKE '%user_response%'`，记录受影响行数应大于 0。
- [x] **二次执行（幂等检验）**：在同一份拷贝上连跑第二次，断言受影响行数必须精确为 **0**。

## 3. from_legacy 边界：发送端与接收端区分

根据“两用一禁”原则，明确 `from_legacy` 的使用边界及落地文件如下：

| 使用场景与原则 | 具体文件:行号 (File:Line) | 处理方式 |
| --- | --- | --- |
| **【用】入口 Pydantic 模型** | `novaic-agent-runtime/queue_service/routes.py` (如 `DispatchRequest` 模型) | 凡是 `trigger_type: TriggerType` 字段，均使用 pydantic validator 调用 `from_legacy` 兼容旧字符串入参。 |
| **【用】DB 读出点** | `novaic-agent-runtime/queue_service/session_repo.py:42` | 读取旧数据记录或 JSON 解析时，调用 `from_legacy` 以宽容接纳尚未被清洗的旧数据。 |
| **【禁】发送构造端** | `novaic-business/business/internal/subagent_utils.py:249`<br>`novaic-business/business/internal/subagent.py:296`<br>`novaic-business/business/schema_push.py:110`<br>`novaic-common/common/tools/definitions.py:512,522` | **禁止**使用 `from_legacy`，必须绝对使用 `TriggerType.USER_MESSAGE.value` 等来构造新数据。 |
| **【禁】SDK 透传调用** | `novaic-agent-runtime/task_queue/client.py:479` | **禁止**使用 `from_legacy`，纯透传或字符串 compare 时一律使用 `TriggerType.XXX.value`。 |

## 4. Metric 标签空间闭合

枚举改造后，PR-10 等将会统一采集 `dispatch_total{trigger_type=...}`。此处确认枚举空间完全闭合，包含以下 6 个合法值：
1. `user_message` (包含由 `user_response` 兼容映射而来的)
2. `subagent_send`
3. `spawn_subagent`
4. `scheduled_wake`
5. `system_wake`
6. `recovered` (仅供 HealthWorker / recovery_worker 在错误重跑时使用，不属常规派发路径，但标签空间必须包含)

## 5. 范围边界与延后项

- **仅处理枚举与 DB 清洗**：本 PR 的目标只将历史脏数据清洗完毕并统一枚举，不对任何调度核心逻辑做变更。
- **单独合并与观察期**：由于本 PR 涉及生产环境 DB 的修改 (`UPDATE subagents ...`)，**必须单独提 PR、单独合并，并在线上单独运行观察至少 24 小时**。确认无脏数据报错后，才能合并后续承接此枚举的 PR-10 `DispatchAssembler`。
- **TD 延后（LLM tool schema 错位）**：`definitions.py` 的 LLM schema 中 `wake_triggers[].type` 的取值 (`timer / event`) 与主流程 `TriggerType` 枚举不对齐，不在此 PR 修复。另开后续 PR 统一，并同步写入 `docs/roadmap/technical-debt.md`。
