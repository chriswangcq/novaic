# Upstream react generation default classification

## Problem Definition

`task_queue/contracts/react_think.py` and `task_queue/contracts/react_actions.py` still default `session_generation` to `0`. These contracts can feed wake-finalize saga creation, so P347 must decide whether P336 needs to change them now or whether P336 is sufficiently protected by fail-closed delivery guards and the upstream cleanup belongs to later P337/P339 work.

## Proposed Solution

1. Inspect `ReactThinkInput.from_context`, `ReactActionsInput.from_context`, and their finalize-trigger payload builders.
2. Inspect tests that assert `session_generation=0`.
3. Determine whether a missing generation can still become an accepted `session.ended` delivery after P341/P342.
4. If yes, fix here or spawn a blocking child. If no, record exact follow-on ownership and the guard evidence showing P336 fails closed.

## Acceptance Criteria

- Classification explains whether upstream defaults block P336 parent success.
- Evidence cites the upstream files/tests and the P341/P342 fail-closed boundary.
- If not fixed here, the result names the downstream ticket(s) that must remove upstream defaults later.

## Verification Plan

- Read `task_queue/contracts/react_think.py`, `task_queue/contracts/react_actions.py`, and `tests/test_runtime_explicit_contracts.py`.
- Run source guards for direct `session.ended` delivery fallback after P341/P342.

## Risks

- Misclassifying upstream defaults as non-blocking could leave a runtime path that fails wake-finalize repeatedly. The result must distinguish "safe for P336 delivery correctness" from "good final architecture".

## Assumptions

- P336 is about session-ended delivery accepting malformed effects; broader react context contract cleanup can be a separate upstream task if bad values fail before delivery.
