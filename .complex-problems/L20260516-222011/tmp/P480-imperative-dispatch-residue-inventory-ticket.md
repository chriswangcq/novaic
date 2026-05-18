# Imperative dispatch residue inventory ticket

## Problem Definition

P480 must create a read-only inventory of old imperative dispatch, fallback, legacy, compatibility, direct saga creation, direct session mutation, and finalize/session-ended residue. This inventory is the evidence base for later cleanup children.

## Proposed Solution

Run focused `rg` guard groups over `novaic-agent-runtime/queue_service`, `novaic-agent-runtime/task_queue`, and relevant tests. Save the raw guard output and a concise classification matrix. Compare git status before and after to prove the child did not modify production source.

## Acceptance Criteria

- Raw guard artifact is saved.
- Classification matrix covers required boundary, test/docs guard, high-confidence removable residue, and ambiguous follow-up candidate buckets.
- File references are specific enough for downstream cleanup.
- Before/after git status proves no source edits were made by this inventory child.

## Verification Plan

Run guard commands from repo root, save output under `.complex-problems/L20260516-222011/tmp/p480/`, then inspect representative hits and record classification. Run no tests unless the inventory unexpectedly changes files.

## Risks

- Keyword scanning can produce false positives in tests/docs.
- Too little classification would force downstream children to rediscover context.

## Assumptions

- P480 is read-only inventory only; cleanup belongs to later children.
