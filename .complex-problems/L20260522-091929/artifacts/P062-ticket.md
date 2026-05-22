# Run Full Entangled Postgres WebSocket Sync Smoke

## Problem Definition

`P062` must run the final WebSocket sync smoke against the Postgres-mode staging runtime and produce the evidence needed for `P052`. The smoke must cover schema/full/head frames, list and stream behavior, write/delta propagation, reconnect safety, persisted sync-version monotonicity, stream ordering with `entangled_rowid`, report redaction, and staging cleanup. A `P061` dry run also exposed that BLOB-backed list rows currently fail WebSocket JSON serialization, so the full smoke must handle that risk explicitly.

## Proposed Solution

Use the `entangled-ws-smoke` client from `P061` against the `P060` staging runtime. Before the final run, prepare a non-BLOB list fixture entity if needed so representative list coverage can be proven without being blocked by the known `blob_data` bytes serialization issue. Run the smoke with stream writes enabled and Postgres DSN evidence enabled, capture a redacted report, verify sync versions do not decrease after write and reconnect, verify `entangled_rowid` ordering/count evidence, check that no tokens/DSNs appear in the report or staging log, and then stop the staging process.

## Acceptance Criteria

- The final smoke report shows WebSocket schema evidence and at least one list/snapshot or equivalent full-sync frame.
- The report shows stream `head_n` evidence for `ws-smoke-stream-events`.
- The report shows a write-triggered delta frame and sync-version monotonicity.
- Reconnect behavior returns `up_to_date`, delta, or another safe non-regressing mode with versions preserved.
- Stream evidence includes count/order or `entangled_rowid` range sufficient to detect duplicate/skipped rows.
- The report and logs contain no raw tokens, JWTs, DSNs, passwords, cookies, or query-string token usage.
- The known BLOB/list serialization issue is either fixed and verified or explicitly isolated by a non-BLOB list fixture with a narrow follow-up recorded later if it remains relevant.
- The staging process on port `19910` is stopped after validation and port cleanup is verified.

## Verification Plan

Run the smoke client remotely with staging token/DSN files and a fixed output path. Query the staging Postgres target through safe file-based DSN access or `docker exec` for version/count/rowid confirmation. Inspect only redacted report/log summaries. After report capture, stop the staging process and verify no listener remains on port `19910`.

## Risks

- Fixing BLOB serialization may be more than this ticket should absorb; a non-BLOB list fixture may be the smaller path for P052 success.
- The staging DB has prior dry-run rows, so the final smoke must use unique IDs and reason over monotonic counts/versions rather than fixed absolute counts.
- If the staging process dies during the run, the result should record partial evidence rather than silently restarting and hiding the failure.

## Assumptions

- `P060` staging process remains running on `127.0.0.1:19910`.
- `P061` smoke client is available both locally and on the API host.
- Production Entangled remains untouched during this validation.
