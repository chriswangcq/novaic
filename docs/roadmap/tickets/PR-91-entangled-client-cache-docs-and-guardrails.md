# PR-91 — Align Entangled client cache docs and guardrails with actual App cache

| Field | Value |
|---|---|
| **Ticket** | PR-91 |
| **Status** | `[✓ deployed]` |
| **Opened** | 2026-04-29 |
| **Owner** | __ |
| **Severity** | P2 architecture clarity — stale docs can make future debugging assume client-side pending ops or write queues that no longer exist. |
| **Depends on** | PR-86 optional. |
| **Blocks** | Cleaner client/Entangled operational runbooks. |
| **Invariant** | The App Entangled cache is a local read model; write/action semantics live in server/action hooks, not a client pending-op table. |

## Background

Client Application Support inspection showed:

```text
entangled_cache.db
  entity_meta
  entity_items
  idx_entity_items_seq
```

There is no `pending_ops` table in the active client cache. Rust cache initialization even drops legacy `pending_ops` if it exists. Any current doc/runbook implying client pending-op cleanup is stale.

## Goal

Update docs and add light guardrails so future debugging matches the actual client architecture:

- client cache is `entity_meta` + `entity_items`;
- `execution-logs` and `messages` are Entangled read-model streams;
- App-side debugging should use the Entangled cache read model, not stale local sidecar storage;
- no active client pending-op path should be assumed.

## Non-Goals

- Do not redesign Entangled.
- Do not add offline write queue semantics.
- Do not change cache schema unless tests reveal drift.

## Implementation Checklist

- [x] Search docs for `pending_ops`, "pending ops", "client write queue", and stale cache-clearing instructions.
- [x] Update Entangled/App docs to describe the actual cache tables.
- [x] Add a troubleshooting snippet for inspecting `entangled_cache.db`.
- [x] Add a guardrail test or lint if there is an existing docs/schema invariant test location.
- [x] Document that historical `log-payloads` was never a default subscribed stream. PR-166C later retired it completely.

## Unit Test Requirements

- [ ] If a schema invariant test exists, assert client cache schema docs match generated/actual Rust cache schema.
- [x] If no suitable unit test exists, add a docs grep guard that rejects reintroducing active-path `pending_ops` instructions.
- [x] Ensure existing Entangled client tests still pass.

Suggested commands:

```bash
pytest novaic-business/tests/test_schema_invariants.py -q
npm --prefix novaic-app run test:unit
cargo test --manifest-path Entangled/packages/client-rust/Cargo.toml
```

Evidence captured 2026-04-29:

```bash
sqlite3 "$HOME/Library/Application Support/com.novaic.app/entangled_cache.db" ".tables"
# entity_items  entity_meta

sqlite3 "$HOME/Library/Application Support/com.novaic.app/entangled_cache.db" \
  "SELECT name FROM sqlite_master WHERE name='pending_ops';"
# no rows

cargo test --manifest-path Entangled/packages/client-rust/Cargo.toml
# 9 passed; 0 failed; 5 doc-tests ignored

scripts/ci/lint_entangled_cache_docs.sh
# passed
```

## Smoke Test Requirements

- [x] Open the App and let Entangled subscribe to `messages` and `execution-logs`.
- [x] Inspect `~/Library/Application Support/com.novaic.app/entangled_cache.db`.
- [x] Verify only expected cache tables are required.
- [x] Verify clearing/restarting the App repopulates subscribed read-model rows.

## Deployment Checklist

- [x] Deploy affected App/Entangled client artifact if the Rust client package is consumed by the shipped App.
- [x] If guardrail code changes are added, run CI and deploy only affected test/CI configuration.
- [x] If App code changes are added, deploy App build.

## GitHub / Commit Checklist

- [x] Commit docs/guardrail changes.
- [x] Commit parent submodule pointer updates if any subrepo changed.
- [x] PR description links this ticket.
- [x] PR description includes grep output for retired stale terms.
- [x] PR description includes one local cache schema sample.

## Acceptance Criteria

- Docs no longer imply active client `pending_ops` behavior.
- Future debugging points to the correct App cache.
- Entangled remains documented as the UI-facing read model, not as a raw LLM/tool payload store.

## Rollback

Rollback only if docs become inconsistent with a deployed older App version. Prefer adding version notes over restoring stale active-path instructions.
