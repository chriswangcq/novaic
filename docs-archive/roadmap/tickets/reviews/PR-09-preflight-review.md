# PR-09 Preflight Review（TriggerType + schema 迁移）

| 字段 | 值 |
| --- | --- |
| Reviewer | senior |
| Verdict | **条件批准**（不是打回；补完 §B 三条后直接开 T1） |
| Target preflight | `docs/roadmap/tickets/reviews/PR-09-preflight-antigravity.md` |

---

## §A  核对结果（file:line 表全部准确）

跨仓 `rg "user_response" --type py` 核对：

| 文件 | 你报的行 | 核对 |
| --- | --- | --- |
| `novaic-common/common/tools/definitions.py` | L512, L522 | ✅ `subagent_rest` LLM tool inputSchema：`"enum": ["user_response", "timer", "event"]` + description `"default: user_response"` |
| `novaic-business/business/internal/subagent_utils.py` | L249 | ✅ `wake_triggers = [{"type": "user_response"}]` |
| `novaic-business/business/schema_push.py` | L110 | ✅ `F.json("wake_triggers", default='[{"type":"user_response"}]')` |
| `novaic-business/business/internal/subagent.py` | L296 | ✅ `data.get("wake_triggers", [{"type": "user_response"}])` |

TS / Rust 零命中核对通过。

**最重要的发现是 `definitions.py`**：这是 LLM tool schema，LLM 产出的 wake_triggers 会直接落 DB，比业务代码里 hard-code 危险得多。这个 catch 很赞。

---

## §B  必须补进 preflight 的 3 条 scope 漏洞

### B.1  `definitions.py:504` 的 enum 是 `["user_response", "timer", "event"]` —— 你没说 `timer / event` 怎么办

真语义冲突：`TriggerType` 6 值里没 `timer / event`。三种路径：

| 方案 | 操作 | 代价 |
| --- | --- | --- |
| **A（推荐）** | 仅替换 `user_response → user_message`，`timer / event` 保留；承认 `wake_triggers[].type` 和 dispatch `trigger_type` 是两个独立 enum、只共享一个值 | 未来 TD：LLM schema 3 值 与 TriggerType 6 值永远不对齐 |
| B | L512 enum 全换成 `TriggerType` 6 值 | LLM 可能输出 `subagent_send` 等无意义 wake condition — 错 |
| C | 扩 `TriggerType` 补 `timer / event` | 反向污染主 dispatch 枚举 — 错 |

**选 A**。在 preflight 里补：

- §1 表后加一句："L512/L522 仅替换 `user_response → user_message`，`timer / event` 保留不动。"
- §5 延后项加一条 TD："LLM tool schema 的 `wake_triggers[].type` 枚举（`timer / event`）与 `TriggerType` 不对齐，另开后续 PR 统一。同步写入 `docs/roadmap/technical-debt.md`。"

### B.2  §3 `from_legacy` 接收端表不完整 + 发送端太抽象

**写清楚"两用一禁"原则**：

- **用 1 — 入口 Pydantic 模型**：任何 `trigger_type: TriggerType` 字段的 validator，用 `from_legacy` 兼容旧字符串入参
- **用 2 — DB 读出点**：解析 `wake_triggers` JSON、读 `session_repo` 旧行时用 `from_legacy`（让还没被 SQL UPDATE 清洗的脏数据可消费）
- **禁 — SDK 透传 / 纯字符串 compare / 发送构造**：一律用 `TriggerType.XXX.value`

**把具体 file:line 填进表**（不要再写"Business 相关模块"、"HealthWorker 等触发点"）：

- 发送端必改：`subagent_utils.py:249` / `subagent.py:296` / `schema_push.py:110` / `definitions.py:512,522`
- 发送端已正确（无需改）：`scheduler_worker_sync.py:164`（发 `"scheduled_wake"`）
- 接收端用 `from_legacy`：`queue_service/session_repo.py:42` + 所有 `trigger_type: TriggerType` Pydantic 字段（跑 `rg "trigger_type.*TriggerType" --type py` 列出全集）
- SDK 透传不用 `from_legacy`：`task_queue/client.py:479`

生产数据迁移 PR 必须 file:line 级精度，不能抽象描述。

### B.3  SQL `REPLACE` 的引号边角 case 没验证

ticket 给的 SQL：
```sql
REPLACE(wake_triggers, '"user_response"', '"user_message"')
```

匹配的是**带双引号**的 `"user_response"`。如果生产 DB 里 JSON 序列化用了单引号或无引号（旧代码 / 不同客户端），这条 UPDATE 会**漏**数据。

**§2 测试 checklist 加一条**：

- [ ] 先 sample 5-10 条真实 `wake_triggers` 行，确认 JSON 字符串是严格双引号；如果混格式，补一版 `REPLACE("'user_response'", "'user_message'")`。

---

## §C  其他都 OK

- §4 metric 标签空间 6 值列全 ✅
- §5 范围边界明确"单独合并 + 24h 观察" ✅
- §2 幂等测试已写 ✅

---

## §D  进 T1 的纪律（生产数据 PR）

1. 补完 §B 三条后**直接开 T1，不用再过一轮 review**。
2. **严禁**在 T1 里遇到新发现的文件偷偷加进 file:line 表 —— 全部回到 preflight 补后再改代码。这是生产数据 PR 的纪律底线。
3. Declare done 前必跑：

```bash
# 净空扫描
rg "'user_response'" novaic-*/ | rg -v "tests/|from_legacy|migrations/"
# 预期为空

# 幂等验证（拷贝 DB 跑两次）
cp ~/.novaic/data/entangled.db /tmp/entangled-copy.db
sqlite3 /tmp/entangled-copy.db < scripts/migrations/2026-XX-XX-wake-triggers-rename.sql  # N > 0 行变更
sqlite3 /tmp/entangled-copy.db < scripts/migrations/2026-XX-XX-wake-triggers-rename.sql  # 0 行变更

# 单测
PYTHONPATH=novaic-common pytest novaic-common/tests/test_trigger_types.py -v
```

4. `git status --short` 全清 + 每个 `[x]` 反向 `rg` 自检。
