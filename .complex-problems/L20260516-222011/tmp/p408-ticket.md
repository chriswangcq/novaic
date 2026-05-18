# Generic Queue infrastructure classification ticket

## Problem Definition

Generic Queue infrastructure contains generation and defaulting patterns that are likely FSM state mechanics rather than live session-generation compatibility. They must be classified precisely so the final audit distinguishes generic infrastructure state from session authority.

## Proposed Solution

Inspect the P402 hits in:

- `novaic-agent-runtime/queue_service/queue_db.py`
- `novaic-agent-runtime/queue_service/saga_repo.py`
- `novaic-agent-runtime/queue_service/task_fsm.py`
- any generic FSM-related helpers surfaced by the guard

Classify each hit as generic FSM generation/version/counter, task retry counter, already-patched session-adjacent authority, or dangerous residue. Patch only if a hit can mutate live session state without explicit generation validation.

## Acceptance Criteria

- Every generic Queue infrastructure hit from P402 is classified.
- No generic infrastructure hit is misclassified as harmless if it can write live session authority.
- Any dangerous session-adjacent default is patched and tested.
- Generic FSM state mechanics remain only with clear evidence.

## Verification Plan

- Run targeted guards over `queue_db.py`, `saga_repo.py`, `task_fsm.py`, and generic FSM files.
- Inspect surrounding code for each hit cluster.
- Run focused tests for generic FSM store, saga compensation/recovery, task FSM, and suspected-dead recovery if needed.

## Risks

- Generic `generation` in task/saga/lease FSMs is valid infrastructure; removing it mechanically would be worse than leaving it.
- `saga_repo.py` also contains session-adjacent suspected-dead recovery logic, so classification must separate generic saga FSM from session event authority.

## Assumptions

- Generic FSM generations may start at zero if they are not session active-generation authority.
- Live session-adjacent generation writes still require explicit validation.
