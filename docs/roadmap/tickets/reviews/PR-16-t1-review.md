# PR-16 T1 Rework Notes (CONDITIONAL REJECT)

**Verdict**: 代码功能基本正确，但**提交纪律再次崩塌**。两个重复犯错 + 一个虚假测试，必须返工后才能进入 Canary 观察期。

---

## 💥 Blockers（必须修复后重新 Declare Done）

### B.1 【假勾复发】Ticket body 全部未勾但 Status 已打 `[x]`

`docs/roadmap/tickets/PR-16-dispatch-subscriber-full.md`：

- Line 8 **`Status: [x]`** ✅ 已打勾
- Line 30-31 Prerequisites `[ ] [ ]` ❌ 未勾
- Line 117-126 实施清单 **10 个** `[ ]` ❌ 全未勾
- Line 138-145 测试清单 **8 个** `[ ]` ❌ 全未勾
- Line 149-154 Metrics **5 个** `[ ]` ❌ 应打成 `[-] defer to PR-32`（现在是死待办）
- Line 158-160 文档 **3 个** `[ ]` ❌ 全未勾

**这是 PR-06 时我明确点名的"假勾"问题的第二次复发**。Status 是总开关，body 是逐项交付凭证。Status 勾了 body 没勾等于在产品经理面前签到却没写代码。

**修复要求**：
- 真实已完成项 → `[x]`
- Defer 到别的 PR → `[-] (defer to PR-32)` 并注明具体 PR 号
- 没做的 → 保持 `[ ]` 并在提交说明里明确告知未做
- Status `[x]` 只有在所有非 defer 的行全部 `[x]` 或 `[-]` 之后才允许打

### B.2 【提交不完整】preflight 改动未 commit，宣称"全量提交"失实

```
M docs/roadmap/tickets/reviews/PR-16-preflight-antigravity.md
?? docs/roadmap/tickets/reviews/PR-16-preflight-review.md  (这是我写的 review，忽略)
```

你根据我的 review 更新了 preflight 里的 Pydantic schemas、DLQ 决策、`outbox_client` 注入方案（diff 里明显看到 §1、§2 内容被大改），但**这些改动一个都没 commit**。

"所有改动全量提交"的宣告是错的。

**修复要求**：
```bash
git add docs/roadmap/tickets/reviews/PR-16-preflight-antigravity.md
git commit -m "docs: PR-16 preflight updated per review (wire schemas, DLQ semantics, client injection)"
```

### B.3 【测试造假】`test_expired_lock_reclaimed` 是假测试

`novaic-business/tests/test_dispatch_subscriber.py:115-138`：

```python
mock_outbox_client.post.return_value = Response(200, ..., json={"rows": [{"id": 4, ...}]})
rows_a = await sub_a._claim_batch()  # mock 返回 id=4
# Worker B
rows_b = await sub_b._claim_batch()  # mock 还是返回 id=4
```

两次 claim 拿到"同一行"是因为 `mock_outbox_client.post.return_value` 被硬编码成固定响应——**跟 TTL 过期、跟 DB fencing 一点关系都没有**。你断言的只是"两次调用都传了 `claim_ttl_ms=100`"（这是参数传递测试，不是 crash 恢复测试）。

我 §H 的原话："Worker A claim → 睡 150ms → Worker B claim → 验证 Worker B 拿到同一行"——需要的是**真 DB 层**的 TTL 过期语义验证。

**修复要求**：把这个测试搬到 `Entangled/packages/server-python/tests/test_outbox_endpoints.py`，用真 sqlite + `asyncio.sleep(0.15)` 验证：

```python
def test_claim_ttl_expires_and_reclaims(client, db):
    db.execute("INSERT INTO message_outbox (message_id, agent_id, trigger_type, payload_json, created_at) VALUES ('msg_recover', 'agt_1', 'USER_MESSAGE', '{}', 1000)")
    
    # Worker A claims with 100ms TTL
    r1 = client.post("/v1/outbox/claim", json={"worker_id": "w_a", "claim_ttl_ms": 100})
    assert r1.json()["count"] == 1
    row_id = r1.json()["rows"][0]["id"]
    
    # Worker B immediately → 0 rows (A holds lock)
    r2 = client.post("/v1/outbox/claim", json={"worker_id": "w_b", "claim_ttl_ms": 100})
    assert r2.json()["count"] == 0
    
    # Wait for TTL expiration
    import time; time.sleep(0.15)
    
    # Worker B claims → gets SAME row (this is the real recovery semantic)
    r3 = client.post("/v1/outbox/claim", json={"worker_id": "w_b", "claim_ttl_ms": 100})
    assert r3.json()["count"] == 1
    assert r3.json()["rows"][0]["id"] == row_id  # SAME DB row
    
    # Verify locked_by swapped
    db_row = db.execute("SELECT locked_by FROM message_outbox WHERE id = ?", (row_id,)).fetchone()
    assert db_row["locked_by"] == "w_b"
```

同时把 business 端那个假测试要么删掉要么改成纯参数传递测试（`test_claim_ttl_is_passed_through`），不要伪装成 crash recovery。

---

## ⚠️ 高优先级问题（本次返工顺带修）

### H.1 `test_subscriber_transient_failure` 使用不存在的 `kind`

`novaic-business/tests/test_dispatch_subscriber.py:73`：

```python
mock_assembler.dispatch.side_effect = DispatchError(kind="queue_500", msg="Service Unavailable")
```

`DispatchError.kind` 的 `Literal` 定义是 `"bad_argument"|"no_owner"|"queue_400"|"queue_5xx"|"network"`——根本**没有 `queue_500`**。

测试之所以过，是因为 dataclass 不做 runtime Literal 校验（我已实测确认）。但这个测试在测一个生产代码**永远不会产生**的幽灵错误。改成 `kind="queue_5xx"`。

### H.2 `mark_failed` 永久态用 `attempts=999999` 抹掉真实计数

`Entangled/.../outbox.py:121`：

```python
if req.permanent:
    attempts = 999999  # ← magic sentinel
```

功能上能让行"永久不被再 claim"（因为 `attempts < max_attempts=5` 成立失败），但**真实 attempts 计数被烧掉了**。PR-26 orphan emitter 将来无法区分"第 1 次就永久失败（bad_argument）"和"重试 5 次耗尽（queue_5xx）"——这是两个完全不同的事故信号。

**修复方案（任选）**：
- (A) 在 `MarkFailedRequest` 加 `attempts_to_set: Optional[int]`，client 传入实际 `attempts+1`，server 保真。Permanent 时额外写个 `poisoned = 1` 字段或在 claim 的 SQL 里加 `AND last_error NOT LIKE 'permanent:%'`。
- (B) 在 outbox 表加个 `status` 列：`'pending' | 'poisoned' | 'delivered'`，claim 的 `WHERE status = 'pending'`，permanent 时 `SET status = 'poisoned'`。`attempts` 保持真实。

我倾向 (B) 因为语义更清晰。但你选 (A) 也 OK，只要不丢失真实 attempts。

**如果决定本 PR 不改**（理由：PR-26 orphan 还没写到），请在 `docs/roadmap/technical-debt.md` 明确登记："PR-16 `mark_failed` 用 999999 哨兵烧毁真实 attempts 计数，PR-26 orphan emitter 依赖 attempts 区分事故类型时必须先返工 outbox schema"。

### H.3 主仓 commit 又把 submodule bump 和 docs 绑一起

`1dc4e11` 同时包含：
- `Entangled`/`novaic-business` pointer bump
- `PR-16-dispatch-subscriber-full.md` 状态更新
- `PR-32-metrics-prometheus-integration.md` 新增 5 条

我的 preflight review §J 写的是"`chore: bump submodules for PR-16` + `docs: PR-16 checked off + metrics defer to PR-32`"——格式上用 `+` 造成了歧义，这一半是我的锅。但 PR-15 `44dca1c` 事件已经明确过精神：**submodule bump 和 docs 必须分两个 commit**。

**下次严格遵守**：
```
chore: bump submodules for PR-16
docs: check off PR-16 + append PR-32 metrics from subscriber
```

本次不要求重写历史修补，但 B.1 修假勾时会自然产生新的 `docs:` commit，单独提即可。

---

## 📝 Minor（TD 登记即可，不阻塞）

- **M.1** `_claim_batch` 捕获异常返回 `[]` 时 `logger.exception` 每 `poll_interval=0.5s` 打一次。Entangled 故障 1 天产生 172800 条错误日志。登记 TD："subscriber 连续 claim 失败时需要 error backoff / rate-limited logging"。
- **M.2** `_mark_delivered` 失败场景：dispatch 已发但 outbox 没标 delivered，30s 后另一 worker 重 claim → 重发 → Queue 用 `action=deduped` 拦截。功能安全但会产生重复 `subscriber_delivered` log。在 `_mark_delivered` 处加注释 "若此处失败依赖 Queue idempotency ledger 兜底去重"。
- **M.3** Entangled 端测试用 `FakeDatabase` 而非真 Database wrapper，没覆盖事务语义。本 PR 不要求，但等 PR-23（outbox backlog metric）要跑真 DB 路径时必须补。

---

## ✅ 做得好的地方（客观记录，不是安慰）

- 6 个独立 commit 在 submodule 层拆得干净，feat/test 分离到位（除了主仓那单）
- Pydantic schemas 完整覆盖 5 个 model，`Depends(verify_service_or_user)` 全挂
- `_deliver_one` 的 `JSONDecodeError → permanent` 按 §I 落地
- Graceful shutdown 在 batch 中间 check `_stop.is_set()`（G.2 语义精确）
- `from_legacy` 转 `TriggerType`、`DispatchResult.raw.get("action")` 读 Canary 信号——两处决策点按 review 一次到位
- `outbox_client` 构造器注入，lifespan 里按 `internal_async_client(service_name="business-subscriber")` 正确 wire
- PR-32 metrics backlog 新增的 5 条（`subscriber_delivered_total` 等）都列出来了

---

## 📋 返工 Checklist

提交前自检：

- [ ] B.1 Ticket body 逐行核对 `[x] / [-] / [ ]`，Status 才允许 `[x]`
- [ ] B.2 `git status --short` 在主仓 + 所有子模块都是干净的
- [ ] B.3 Entangled 新增 `test_claim_ttl_expires_and_reclaims`，business 端假测试删除/改名
- [ ] H.1 `queue_500` → `queue_5xx`
- [ ] H.2 选 A/B 方案或登记 TD（必须三选一，不允许沉默）
- [ ] Declare Done 前把修复按 feat/test/docs 拆 commit，别把 B.1 的 ticket 勾选和 H.1 的测试 fix 塞同一个

返工后贴：
1. 测试输出（`pytest -v` 带时间戳）
2. 新 `test_claim_ttl_expires_and_reclaims` 的单独输出，证明用了 `time.sleep(0.15)` + 真 DB
3. Ticket 勾选状态截图或 `rg '^- \[[ x/-]\]' docs/roadmap/tickets/PR-16-dispatch-subscriber-full.md` 的输出

---

## 🎯 元提醒（第三次）

PR-06 假勾 → PR-15 bundle commit → PR-16 假勾 + 假测试。

**三种"直觉上省事的小聪明"在这一条时间线上已经复发了**：
1. 假勾：状态光鲜但凭证缺失
2. bundle commit：提交省一次，review 难一倍
3. 假测试：测试过了但覆盖面是幻觉

这三类错误的共性是 **"交付时的自我审查缺位"**。Declare Done 前强制问自己三遍：

- "我勾的每一项都对应一段可执行凭证吗？" → 反假勾
- "这个 commit 能独立 revert 且不破坏 bisect 吗？" → 反 bundle
- "这个测试如果我去掉生产代码它会红吗？" → 反假测试

Canary 观察期不能在假 Declare Done 上启动。返工搞完再进入。

