# Synthesize Gateway and Cortex SQLite Dispositions

## Problem Definition

Gateway and Cortex have now been classified separately. P010 still needs a combined disposition artifact and the central SQLite classification note must reflect the current Gateway/Cortex boundary if it is stale.

## Proposed Solution

Create a combined synthesis and update the central note only if needed.

1. Read P021 and P022 artifacts.
2. Read the current `/opt/novaic/data/SQLITE_STATE_CLASSIFICATION.md` on the `api` host.
3. Write `.complex-problems/L20260522-091929/artifacts/gateway-cortex-sqlite-boundaries.md` summarizing:
   - Gateway tables to migrate, not migrate, and back up;
   - Cortex tables to migrate and back up;
   - future Postgres DB targets;
   - no-cutover status.
4. If the central note lacks these current dispositions, append a timestamped documentation-only section to it.
5. Verify the remote note if changed.

## Acceptance Criteria

- A durable combined artifact exists.
- Gateway and Cortex dispositions match P021 and P022.
- Backup expectations and Postgres targets are summarized.
- The central classification note is updated if stale, or no-update rationale is recorded.
- No service data, schema, runtime config, or cutover is changed.

## Verification Plan

- Verify the combined artifact exists and includes Gateway and Cortex sections.
- If remote note is updated, verify it contains the new timestamped section.
- Verify Gateway and Cortex health/readiness after any documentation write.
- Record the result and run a problem-level success check.

## Risks

- The central note is on the production host, so the update must be documentation-only and minimal.
- Rewriting the whole note could accidentally remove prior classification context; prefer append.
- Service health checks should be run after the documentation update.

## Assumptions

- P023 may write only documentation, not SQLite data or service config.
- Gateway and Cortex classifications from P021/P022 are authoritative for this synthesis.
