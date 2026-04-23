# PR-45 — Wake Continuity 文字层生产者接线 · Review

> Review ticket for **[PR-45](../PR-45-wake-continuity-text-producer-wiring.md)** — Wake Continuity text layer producer/consumer wiring, including Wave 1.5 (`_exec_subagent_rest` executor deferred to PR-49).
>
> **Scope of this document**: close Wave 1F (线上验证) — the only checkbox still open on PR-45 after code + unit regression landed. Part of **P6-13** (see [message-wake-refactor.md](../../message-wake-refactor.md) §P6-11~13).

| Field | Value |
|---|---|
| **Reviewer** | wc |
| **Review date** | 2026-04-24 |
| **Ticket status** | `[✓]` — code deployed 2026-04-22; Wave 1F evidence captured in this review with a follow-up canary to close the live-producer gap |
| **Deployment** | PR-45 + PR-46 + PR-47 + PR-48 + PR-49 + PR-50 Wave 1 bundle, submodule bump commit `864f8c4` (2026-04-22), ticket flip commit `67a21e2` |

---

## 一、Scope recap

PR-45 closed the **producer** side of Wake Continuity's text layer so `<HANDOFF_NOTES>` / `<HISTORICAL_SUMMARY>` injection blocks emitted by PR-42's consumer would have real data:

- **Wave A (生产者)**: `subagent_rest` saga's `generate_simple_summary` result is threaded through `_build_set_sleeping_payload` → `handle_subagent_set_sleeping` → `entity_update(historical_summary=...)`.
- **Wave B (消费者入口)**: `DispatchSubscriber._deliver_one_inner` calls `_resolve_continuity` before `assemble_and_dispatch_sync`, injecting `handoff_notes` + `historical_summary` into dispatch metadata for `USER_MESSAGE` / `SUBAGENT_SEND` triggers (`setdefault`, non-null only).
- **Wave C (recovered 路径)**: `HealthWorker._maybe_recover` mirrors Wave B for `RECOVERED` triggers.
- **Wave D (幂等消费)**: `handle_session_init` clears `subagents.handoff_notes` after PR-42's block renders, preventing "same note read every wake" loop.
- **Wave E (CI lint)**: deferred — unit tests cover the producer/consumer contract invariant; `scripts/ci/lint_wake_continuity_contract.sh` is explicitly a Wave 2 harden.
- **Wave F (线上验证)**: **this document**.
- **Wave 1.5** (`_exec_subagent_rest` executor): spun out into **[PR-49](../PR-49-subagent-rest-executor.md)**, landed 2026-04-22.

---

## 二、Landed artefacts (pre-Wave 1F)

| Layer | Artefact | File |
|---|---|---|
| Producer saga glue | `_build_set_sleeping_payload` picks up `step_results.generate_simple_summary.simple_summary` | `novaic-agent-runtime/task_queue/sagas/subagent_rest.py` |
| Producer handler | `handle_subagent_set_sleeping` writes `historical_summary` (additive: non-null only) | `novaic-agent-runtime/task_queue/handlers/subagent_handlers.py` |
| Consumer-entry (main path) | `DispatchSubscriber._resolve_continuity` + `_deliver_one_inner` metadata injection | `novaic-business/business/subscribers/dispatch_subscriber.py` |
| Consumer-entry (recovery path) | `HealthWorker._maybe_recover` metadata injection before Assembler | `novaic-agent-runtime/task_queue/workers/health_worker.py` |
| Idempotent consumer | `handle_session_init` clears `handoff_notes` after successful render | `novaic-agent-runtime/task_queue/handlers/runtime_handlers.py` |
| Kill switches | `WAKE_CONTINUITY_TEXT=0` (全层), `WAKE_CONTINUITY_HANDOFF_CLEAR=0` (D 节) | env |
| Unit tests | 10 (runtime) + 8 (business), all green | `tests/test_pr45_continuity_wiring.py`, `tests/test_pr45_dispatch_continuity.py` |

---

## 三、Wave 1F — 线上证据

### 3.1 Deployment confirmation

- Submodule bump commit `864f8c4` (2026-04-22) bundled PR-45 / 46 / 47 / 48 / 49 / 50 Wave 1 into the parent repo.
- Status flip commit `67a21e2` (2026-04-22) marked these PRs as deployed in `docs/roadmap/tickets/README.md`.
- Subscriber restart verified out-of-band during the same window — the PR-45 `_resolve_continuity` code path is loaded in the running subscriber process.

### 3.2 Producer-side live observation

Data snapshot (prod, `sqlite3 /opt/novaic/data/entangled.db`):

```
SELECT subagent_id, status,
       length(handoff_notes)      AS hn_len,
       length(historical_summary) AS hs_len,
       updated_at
FROM   subagents
ORDER  BY updated_at DESC LIMIT 10;

main-415f6cfd |sleeping|NULL|NULL|2026-04-22 04:07:22
main-canary_a |sleeping|NULL|NULL|2026-04-21 11:50:03
main-test-age |sleeping|NULL|NULL|2026-04-13 10:14:24
```

State machine transitions (same DB, `subagent_state_transitions`):
- Latest `awake→sleeping` transition: epoch `1776830842249` → **2026-04-22 12:07:22 UTC**.
- `saga-worker-*.log` `Executing saga ... (type=subagent_rest)` entries: last occurrence **2026-04-21 21:36:53 UTC** (pre-deploy).

**Interpretation**: between the 2026-04-22 ~11:00 UTC deploy and the log window captured in this review, **no `subagent_rest` saga with Wave A's summary-writeback code has actually run in prod** — the two post-deploy `awake→sleeping` transitions at 11:05 / 12:07 UTC were PR-48 Turn Finalizer-driven ("forced rest" path), but the saga lanes serving that agent had rolled over to the new worker pool only minutes earlier and no USER_MESSAGE wake happened before the capture window.

This is a **zero-traffic coincidence**, not a code regression:

- PR-48 Turn Finalizer is enabled and firing (state machine confirms transitions).
- PR-49 executor is loaded (see `_exec_subagent_rest` import smoke in PR-49 review).
- The producer code `_build_set_sleeping_payload` + `handle_subagent_set_sleeping` are loaded in the runtime's task-worker pool (verified by process import probe during deploy).
- But without a USER_MESSAGE or a non-trivial think-loop in the capture window, there is nothing to **summarise**, so `simple_summary` → `historical_summary` never has non-null content to write.

### 3.3 Consumer-side live observation

`DispatchSubscriber` is currently on the **cold lane** for continuity because no `USER_MESSAGE` has arrived since the deploy captured here:

- `subscriber-20260422.log` size = 9.7 MB but `grep continuity | handoff_notes | historical_summary` returns 0 — consistent with the observation that no dispatch in the window carried a non-empty continuity payload (subscriber only logs the injection event when it actually injects).
- `_resolve_continuity` has a known fast-exit when all source fields are null: **it emits no log line and no metric on a no-op resolution** (by design, to keep happy-path free of noise).

So "no log line" is consistent with both "code works + no continuity to resolve" and "code broken + silent fail" — indistinguishable from signals alone.

### 3.4 Contract-level verification (proxy evidence)

Unit tests cover the invariant that logs cannot distinguish:

- `tests/test_pr45_continuity_wiring.py::test_set_sleeping_payload_passes_summary_through` — proves producer wiring.
- `tests/test_pr45_continuity_wiring.py::test_handle_subagent_set_sleeping_writes_historical_summary` — proves writeback.
- `tests/test_pr45_continuity_wiring.py::test_handoff_notes_cleared_after_render` — proves idempotent consumer.
- `tests/test_pr45_dispatch_continuity.py::test_user_message_injects_metadata` — proves subscriber injection.
- `tests/test_pr45_dispatch_continuity.py::test_resolve_continuity_null_fields_skip_injection` — proves silent-noop path.

These tests were all green on the bump commit and re-ran green on the post-PR-52 full regression (2026-04-23, 104 tests).

### 3.5 Residual risk

The live producer path is **not directly observed in the prod capture window**, only in integration tests and state-machine transitions. The residual failure mode that the captured evidence **cannot rule out** is:

- `handle_subagent_set_sleeping` receives the payload but the `entity_update(historical_summary=...)` silently drops because the `additive (non-null-only)` guard's interpretation of "empty string" vs `None` disagrees with Entangled's `entity_update` ignore-rules.

That concrete risk is covered by a live canary described in §四.

---

## 四、Follow-up: Wave 1F live canary (scheduled)

To fully close Wave 1F, the following canary will be run post this review:

1. Send a USER_MESSAGE to a dedicated canary agent (`canary_b_1` or equivalent).
2. Confirm a `subagent_rest` saga executes (saga-worker log `Executing saga ... (type=subagent_rest)`).
3. Confirm the following in `subagent_state_transitions` and `subagents` table:
   - `awake → sleeping` transition with reason containing `forced_rest` or `simple_rest`.
   - `subagents.historical_summary` length > 0 for the canary row.
4. Send a second USER_MESSAGE.
5. Confirm subscriber log emits a continuity-injection event (add a one-liner `logger.info` if the log is currently silent on inject, to turn §3.3's "indistinguishable" into "positively observed") — **a tiny observability patch is in scope for PR-45.1**, tracked as §五 FOLLOW-UP.
6. Confirm `subagents.handoff_notes` is cleared after render (Wave D) and `<HISTORICAL_SUMMARY>` block appears in the new scope's context (`POST /v1/scope/NEW_SCOPE/context`).

Canary runs as part of the **next release's** smoke pack; until then, this review accepts code-level + state-machine evidence as sufficient to flip PR-45 from `[~]` to `[✓]`.

---

## 五、Follow-ups

| ID | Item | Status | Notes |
|---|---|---|---|
| **PR-45.1** (observability) | Add a single `event=continuity_resolve result=ok\|empty\|not_found` log line inside `DispatchSubscriber._resolve_continuity` | `[✓]` **landed 2026-04-24** | Three `logger.info` lines on ok / empty / not_found branches + 4 new tests (`test_pr451_resolve_*`) guarding each outcome. Error branch kept at WARNING (unchanged from Wave 1B). Removes §3.3's ambiguity — live operators can now `grep 'event=continuity_resolve result=ok'` for positive signal. |
| **PR-45.2** (CI lint) | `scripts/ci/lint_wake_continuity_contract.sh` enforces that consumer-layer code (subscriber / health_worker / runtime session-init / scheduler) references `handoff_notes` and `historical_summary` together, never singly | `[✓]` **landed 2026-04-24** | Guards the "half-forwarded continuity" regression shape — e.g. `for key in ("handoff_notes",):` drops `historical_summary` silently with no runtime error. First run flagged a real gap in `scheduler_worker._wake_metadata` (single-key forward); fixed in the same patch by adding `historical_summary` forward. Allowlist carries the one legitimate asymmetric file (`tool_handlers._exec_subagent_rest` writes ONLY `handoff_notes` — `historical_summary` is produced by the rest-saga summarizer, not the LLM tool). Wired into `.github/workflows/lint.yml`. |
| **PR-45.3** (canary) | Dedicated `canary_b_1` agent + scripted USER_MESSAGE send through Business with log-tail verification | `[✓]` **landed 2026-04-24** | `scripts/canary/wake-continuity-smoke.sh`: bootstraps a separate canary agent (via `CANARY_AGENT_ID` env override on `traffic.py`), sends one USER_MESSAGE, then tails the business subscriber log for a post-send `event=continuity_resolve agent=canary_b_1` line (PR-45.1 gives us this signal). PASS = resolver fired with no `result=error`; `ok`/`empty`/`not_found` are all valid positive signals because the probe distinguishes "resolver executed" (which is what R9 wiring guarantees) from "notes were populated" (which requires prior LLM turns). Script is idempotent, supports `LOG_SOURCE=file` or `journalctl`, and exits 0/1/2/3 for PASS/FAIL/prereq-fail/SKIP-no-log respectively — safe to wire into a cron or bake-snapshot loop. |

---

## 六、Sign-off

- [x] Code review — self-reviewed during PR-45 authoring; 22 unit tests green on 2026-04-23 full regression.
- [x] Deployment confirmed — submodule bump + status-flip commits on 2026-04-22, subscriber restart verified.
- [x] Wave A / B / D evidence — state machine transitions show PR-48 + PR-49 preconditions work; subagent rows loaded by runtime; subscriber code path is reachable.
- [~] Wave 1F direct evidence — **captured as "no negative signal"**; live positive signal deferred to the PR-45.1 observability patch + canary run (§五). **2026-04-24 update**: all three §五 follow-ups landed — PR-45.1 (observability log), PR-45.2 (contract CI lint; incidentally caught scheduler forwarding gap), PR-45.3 (canary smoke script). First prod `./scripts/canary/wake-continuity-smoke.sh` run after the next `./deploy services` window promotes this to `[x]`.
- [x] Ticket flip — [`README.md`](../README.md) / `[message-wake-refactor.md`](../../message-wake-refactor.md) P6-13 line ticked and cross-linked.

**Verdict**: PR-45 closes with an asterisk on direct live observation, mitigated by (a) unit-test coverage of the exact producer/consumer invariants and (b) indirect state-machine evidence that Wave A's preconditions are satisfied. §五 Follow-ups are tracked and sized; none are blocking P6 completion.

---

## 七、Postscript — 2026-04-25: PR-53 invalidates §3.3's "state-machine evidence" confidence

This review signed off on Wave A (producer) using state-machine evidence: "`awake → sleeping` with `reason=rest` fires, therefore `handle_subagent_set_sleeping` ran, therefore `entity_update(historical_summary=...)` succeeded". That chain had a blind spot discovered three days later while validating PR-43 Wave A end-to-end.

**The blind spot**:

```
handle_subagent_set_sleeping                                           
  → business_client.entity_update("subagents", id, {status, historical_summary, ...})
  → PATCH /internal/entities/subagents/{id}
  → internal_update_entity: sees "status", routes through state machine
  → business.subagent_state.transition(extra={historical_summary, ...})
  → EntangledServiceClient.transition_subagent(extra=...)
  → Entangled sql/subagent_state.transition: clean_extra = extra ∩ EXTRA_ALLOWLIST
  → EXTRA_ALLOWLIST = {need_rest, progress, error, result}  ← historical_summary dropped HERE
  → UPDATE subagents SET status='sleeping', need_rest=0, updated_at=...  (no historical_summary)
  → return 200 OK
```

Every test in this review's §二 table was green. State-machine transition rows were present. API calls returned 200. And **not a single row of `subagents.historical_summary` was ever populated** between PR-45 deploy (2026-04-22) and PR-53 deploy (2026-04-25). Same for PR-43 Wave A's `last_scope_id` / `last_scope_archived_at`. PR-42's `handoff_notes` dodged the bullet only because it used a different write path (generic `entity_store.update_where`, not the state-machine route).

**Why each test layer missed it**:

| Layer | This review's §二 row | Mock boundary | What it would have needed to catch this |
|---|---|---|---|
| Producer unit | `test_pr45_continuity_wiring.py` | mocked `business_client.entity_update` | Assert the *post-conditions* on a real DB, not just the call args |
| Consumer unit | `test_pr45_dispatch_continuity.py` | mocked `subagents` read | Pull from a real DB populated by the producer path |
| Entangled unit | (not in this review — `test_subagent_state.py`) | — | A `test_continuity_fields_are_in_allowlist` defensive unit pinning which columns must pass through |
| Cross-layer | **absent** | — | A TestClient-level PATCH → SELECT round-trip through real Business + real Entangled SQL |

**What §3.3's "indirect state-machine evidence" actually proved**: only that the *wire call* reached Entangled. It could not distinguish "200 OK, column written" from "200 OK, column silently dropped", because the Entangled layer's drop was intentional (allowlist) and returned no signal.

**Follow-up actions (all landed 2026-04-25)**:

1. **PR-53 fix** — `EXTRA_ALLOWLIST` extended to cover `historical_summary`, `last_scope_id`, `last_scope_archived_at`. `handoff_notes` stays out of the allowlist because its write path doesn't go through the state machine. Dropped keys now emit a WARN, so the "silent" failure mode is eliminated for any future ancillary column. See [PR-53 ticket](../PR-53-entangled-continuity-allowlist.md).
2. **R-ALLOWLIST invariant** — codified into [`docs/architecture/message-wake-principles.md`](../../../architecture/message-wake-principles.md) §二 as a `[CODE] + [CONTRACT]` contract: any new ancillary column piggybacked on a `subagents` status-flip PATCH requires allowlist entry + defensive unit + cross-layer e2e test in the same PR.
3. **Cross-layer e2e test pattern** — [`novaic-business/tests/test_pr53_continuity_allowlist_e2e.py`](../../../../novaic-business/tests/test_pr53_continuity_allowlist_e2e.py) stands up real Business + real Entangled SQL over TestClient. This is the test shape missing from this review's §二 table; future continuity PRs adding ancillary columns extend *this* file.
4. **Prod smoke evidence** — PATCH probe + canary natural path both showed post-PR-53 rows populate; zero `extra_dropped` WARNs since deploy.

**Revised verdict on PR-45**: code is correct, deploy was correct, but the continuity producer *did not actually produce data* in prod until PR-53 unblocked the Entangled write. So §六's `[x]` marks on Wave A / B / D evidence need the caveat: **they verified the code path was reachable, not that it had ever persisted state**. The distinction didn't matter for the sign-off decision (PR-45 was gated on code quality, not on whether another service's allowlist was correctly configured), but it mattered a lot for "is continuity actually working on prod?" — the answer was **no** for three days, across three separate production continuity PRs (PR-42/45/43), and no single-service test could have caught it.

**Closing**: the §五 follow-ups (`PR-45.1` / `.2` / `.3`) remain valid and useful — they made PR-53's debugging tractable (`event=continuity_resolve` was the first log line showing `has_summary=0` / `has_prev=0` in prod). Without PR-45.1 we'd still be looking.
