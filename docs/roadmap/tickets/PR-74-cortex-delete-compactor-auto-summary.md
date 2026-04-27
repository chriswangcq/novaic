# PR-74 — Delete Cortex auto-summary / Compactor path

| Field | Value |
|---|---|
| **Ticket** | PR-74 |
| **Status** | `[✓]` |
| **Opened** | 2026-04-27 |
| **Owner** | __ |
| **Severity** | P0 Cortex boundary — automatic summary is a second memory path and conflicts with explicit child-skill summary semantics. |
| **Blocks** | PR-75, PR-76, PR-77 |
| **Blocked by** | PR-70, PR-73 |
| **Invariant** | The only durable summary path is: LLM opens a child skill, then closes that child with `skill_end(report=...)`; that report is persisted verbatim as that child scope's `summary.md`. |

## Intent

Hard-delete the remaining Cortex auto-summary machinery.

Cortex should not infer, generate, or fallback-create summary text. It maintains the LIFO scope tree and renders that tree into LLM context. Summary content is authored only by an explicit `skill_end(report=...)` on a child scope.

## Required Behavior

- Remove or retire `Compactor`, `Summarizer`, and `auto_summary_max_tokens` from active Cortex code.
- Closing a scope without an explicit report must not call an LLM summarizer and must not synthesize fallback summary prose.
- `summary.md` is written only from the explicit close report of a real child scope.
- Wake/lifecycle/root/meta scopes are structural containers and are not summary producers.
- Any legacy API or facade that can still trigger report-less compaction is deleted or converted to fail-fast explicit-report-only behavior.

## Acceptance Criteria

- Searching Cortex source for auto-summary concepts finds no active implementation path.
- A report-less close cannot produce non-empty summary text.
- Explicit child `skill_end(report="...")` still persists the exact report.
- Agent-root DFS rendering still folds closed child skills using their explicit `summary.md`.

## Engineering Checklist

### Unit Tests

- `[x]` Cortex test: explicit child close writes exactly the provided report to `summary.md`.
- `[x]` Cortex test: report-less lifecycle close persists no generated body.
- `[x]` Cortex test: no summarizer/compactor fallback is reachable from active scope-close endpoints.
- `[x]` Cortex DFS test: closed child skill with explicit summary still renders in stable DFS order.
- `[x]` Regression search/contract test: active Cortex code contains no `Summarizer`, `auto_summary`, `wake summary`, or `chat_reply`-derived summary path outside tombstone docs/tests.

Evidence:

- `cd novaic-cortex && pytest -q tests/test_pr74_scope_summary_contract.py tests/test_pr56_root_scope_summary.py tests/test_pr67_wake_child_api.py tests/test_skill_lifecycle.py tests/test_engine_config_roundtrip.py tests/test_engine_compact_mapping.py tests/test_engine_config_limits.py tests/test_engine_wiring.py tests/test_incremental_sync.py tests/test_archive_invariants.py tests/test_wave4_metrics.py tests/test_hooks_limits.py tests/test_cortex_chaos.py` → `71 passed in 0.41s`
- `cd novaic-cortex && pytest -q` → `377 passed, 16 skipped in 0.72s`
- `cd novaic-agent-runtime && pytest -q tests/test_pr70_explicit_skill_summary_only.py tests/test_pr58_rest_summary_and_tail_render.py` → `14 passed in 0.07s`
- `cd novaic-business && pytest -q tests/test_pr72_prompt_defaults_contract.py` → `2 passed in 0.01s`
- Active Cortex source grep: `rg -n "Compactor|Summarizer|CompactResult|auto_summary_max_tokens|gem_fusion|__fused__|total_fusions|max_fusion_level|total_tokens_saved|compactions_completed|preview_for_summary" novaic_cortex -g '*.py' || true` → no matches.

### Smoke Tests

- `[x]` In production, create an agent-root child skill and close it with `skill_end(report="PR74_EXPLICIT_REPORT")`; confirm next prepare contains that exact folded summary.
- `[x]` Attempt the old lifecycle report path; confirm it does not render as durable summary.
- `[x]` Inspect prepared LLM context and confirm lifecycle/wake scopes are not shown as memory summaries.

Evidence:

- Production import smoke on `api.gradievo.com`: `{"compactor_spec": None, "constructor_has_summarizer": False}`.
- Production context smoke on synthetic agent `pr74-smoke-agent-1777284515`:
  `{"has_child_report": true, "has_structural_report": false, "message_count": 1}`.
- Cortex log evidence:
  `scope.structural_report_ignored user_id='pr74-smoke-user' agent_id='pr74-smoke-agent-1777284515' scope_id='wake-pr74-1777284515' report_len=51 is_root=False`.

### Deployment

- `[x]` Deploy Cortex with `./deploy cortex`.
- `[x]` Run `./deploy status` and confirm Cortex plus backend dependencies are healthy.
- `[x]` Capture at least two online evidence snippets: API/log evidence for explicit report, and API/log evidence that report-less auto-summary is gone.

Evidence:

- `./deploy cortex` → `✓ novaic-cortex 已部署（全部服务已重启）`.
- `./deploy status` → Entangled, Gateway, Business, Device, Queue, Storage-A, Cortex healthy; Workers `8`; Relay active.
- Online evidence captured from import smoke, context prepare smoke, and `scope.structural_report_ignored` log line above.

### GitHub / Commit

- `[x]` Commit implementation and tests as one PR-sized Cortex commit.
- `[x]` Commit message should reference PR-74 intent.
- `[x]` Push the branch and include unit test output, smoke evidence, and deploy evidence in this ticket.

Evidence:

- Cortex submodule commit: `59a511d cortex: delete auto summary compactor path`.
- Pushed to `novaic-cortex/main`.

## Out of Scope

- Business memory/profile/task features.
- User profile extraction or prompt design.
- Migrating old historical scope data beyond proving the new path no longer reads it as summary memory.
