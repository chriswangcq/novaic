# Sandboxd process-boundary success check

## Summary

Success for the narrow P003 scope. The sandboxd package is guarded as a
process-only service, and verification covered both code-level imports/terms
and the existing execution contract tests. This does not claim the whole
LogicalFS migration is done; P004/P005 still own broader Blob boundary and final
verification work.

## Evidence

- R002 added `novaic-sandbox-service/tests/test_sandbox_boundary.py`.
- R002 verified sandbox-service tests pass: `13 passed`.
- R002 recorded a focused residue scan with no matches for Cortex/Blob/Workspace
  ownership terms in `novaic-sandbox-service/sandbox_service`.
- R002 recorded deployment script pointers showing sandboxd remains a separate
  process service on `19994`.

## Criteria Map

- Guard tests fail if sandbox-service imports Cortex or Blob modules -> R002
  added AST import guard for `novaic_cortex`, `blob_service`, and `logicalfs`.
- Guard tests fail on obvious ownership vocabulary -> R002 added term guard for
  `Workspace`, `CortexStore`, `BlobCortexStore`, `agent_id`, `scope_id`,
  `subagent`, `/ro/`, and `/rw/`.
- Existing sandbox-service tests pass -> R002 reports `13 passed`.
- Deployment scripts continue to reference sandbox-service as process service ->
  R002 deployment scan.

## Execution Map

- T003 -> R002. Added guardrail tests and verified sandbox-service behavior.

## Stress Test

- Failure mode: future sandboxd imports Cortex to inspect workspace state. The
  AST import guard fails.
- Failure mode: future sandboxd starts owning subagent or `/ro` `/rw` semantics
  in source. The term guard fails.
- Failure mode: guard is too broad and blocks generic mount behavior. Current
  sandbox-service tests pass, including mount-plan execution.

## Residual Risk

- Non-blocking: this checks sandbox-service source, not sandbox-sdk docs. SDK
  still carries generic mount contracts, which is allowed.
- Non-blocking: parent migration still has open P004/P005.

## Result IDs

- R002

## Blocking Gaps

- none
