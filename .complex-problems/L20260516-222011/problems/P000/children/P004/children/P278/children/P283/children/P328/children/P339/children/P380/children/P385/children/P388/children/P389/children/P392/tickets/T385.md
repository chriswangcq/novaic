# Classify audit and generic FSM generation hits

## Problem Definition

The widened guard still finds generation-like defaults in audit/projection code and generic task/saga/lease FSM infrastructure. These need classification to avoid leaving misleading residue or over-patching safe counters.

## Proposed Solution

Split audit/projection hits from generic FSM infrastructure hits. Patch only live authority paths that accept stale/malformed session generation. Classify safe version/counter/projection adapters with file evidence and tests where useful.

## Acceptance Criteria

- Audit/projection generation hits are classified as safe display/projection adapters or patched.
- Generic task/saga/lease FSM generation hits are classified as separate machine-version counters or patched if they accept stale external input.
- Focused tests pass for any touched modules.
- Final matrix distinguishes session generation authority from generic FSM state versioning.

## Verification Plan

Run targeted `rg` guards for audit/projection files and generic FSM files, inspect representative code, run compile/tests for touched modules, and record a classification matrix.

## Risks

- Treating generic FSM `generation` as session generation could cause needless churn.
- Ignoring these hits without classification would keep confusing residue.

## Assumptions

- Generic task/saga/lease `generation` fields are likely internal FSM state versions, not user/wake session generation, but this must be verified.
