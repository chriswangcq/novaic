# Task Saga Worker FSM Focused Tests Ticket

## Problem Definition

P511 needs focused verification beyond the session/outbox/finalize group. P518 covers the task/saga/worker side: generic FSM substrate, task queue FSM, saga FSM, worker lease/generic worker, queue control plane, busy behavior, and recovery behavior.

## Proposed Solution

Use the P513 selected focused test inventory as the source of truth. Build a P518-specific test target list for task/saga/worker/FSM/control-plane coverage, run pytest from `novaic-agent-runtime`, and record exact target count, command, exit code, and pytest summary.

## Acceptance Criteria

- The P518 focused subset contains only real `test_*.py` files.
- The subset exits successfully.
- The result records exact file count, pytest pass count, and log path.
- Any failure is converted into explicit follow-up work instead of hidden.

## Verification Plan

- Save the P518 target list and a count artifact.
- Run pytest from `novaic-agent-runtime` using that target list.
- Save the pytest log and exit code.
- Check for empty-suite, wrong-path, and partial-run false positives before closing.

## Risks

- The filter could accidentally omit relevant worker/FSM tests.
- The subset could include an unrelated broad test and make failures noisy.
- A green focused subset does not replace the later P511 aggregate check.

## Assumptions

- Existing dirty worktree changes are intentional and must not be reverted.
- P513 selected focused test inventory is the authoritative candidate list.
