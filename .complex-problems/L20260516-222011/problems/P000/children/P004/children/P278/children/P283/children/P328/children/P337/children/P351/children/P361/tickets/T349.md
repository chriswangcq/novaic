# Map recovery and compensation finalize sources

## Problem Definition

P361 must produce a precise map of every recovery or compensation path that can synthesize `wake_finalize` or equivalent finalize mutation work. Without this map, later fixes may harden only the obvious path while leaving an old recovery branch live.

## Proposed Solution

Perform a read-only source audit over `queue_service/saga_repo.py`, `queue_service/session_recovery.py`, saga FSM/outbox code, and focused tests. Search for `wake_finalize`, `finalize`, compensation task creation, session recovery, generation propagation, and any recovery-created saga/task payload. Summarize each path with its source of `scope_id`, wake/root scope path, subagent identity, and session generation.

## Acceptance Criteria

- Every production path under `queue_service` that mentions or creates `wake_finalize` is listed.
- Compensation path identity sources are described separately from session recovery path identity sources.
- Related tests are listed so downstream implementation tickets know where coverage exists or is missing.
- Ambiguous or missing identity paths are explicitly called out for P362 or P363 instead of treated as safe.

## Verification Plan

Use `rg` and targeted file reads (`nl`/`sed`) to inspect production and test paths. The result should cite file/line ranges and include a small table of source paths, identity fields, and risk classification.

## Risks

- Terminology may vary between `wake_finalize`, `session_ended`, compensation, and recovery; search terms must be broad enough to catch indirect paths.
- Test-only helpers may look like production behavior; the source map must distinguish production from tests.

## Assumptions

- This ticket is read-only; it should not modify runtime code.
- Later P351 children will implement fixes for any ambiguous paths found here.
