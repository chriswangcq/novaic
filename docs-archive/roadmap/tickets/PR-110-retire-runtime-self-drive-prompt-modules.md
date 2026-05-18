# PR-110 — Retire Runtime self-drive prompt modules

| Field | Value |
| --- | --- |
| **Ticket** | PR-110 |
| **Status** | `[✓]` |
| **Scope** | `novaic-agent-runtime/task_queue/utils` |
| **Depends on** | PR-99, PR-105 |
| **Invariant** | Runtime must not keep a second prompt/memory/task-planning path based on self-drive profile inference. |

## Problem

The old self-drive prompt modules remain in Agent Runtime:

- `task_queue/utils/self_drive_prompt.py`
- `task_queue/utils/drive_config.py`
- `task_queue/utils/profile_assessment.py`
- `task_queue/utils/task_generator.py`

Current live prompt construction goes through Business drive defaults plus the shared prompt/tool contracts. These four modules are not imported by the active Runtime path; they are a dead parallel concept surface for self-drive prompt generation, profile completeness inference, and automatic task suggestions.

## Goal

- Physically delete the dead Runtime self-drive prompt modules.
- Keep Business product entities such as `drive_config` and task APIs untouched.
- Preserve the current prompt contract: no cold-start user-discovery block, no self-drive task-board block, no automatic profile inference.
- Add a guardrail test so the deleted Runtime modules are not quietly reintroduced.

## Implementation Checklist

- [x] Confirm the modules have no active external imports.
- [x] Delete the four Runtime self-drive modules.
- [x] Add a Runtime guardrail test for file absence and no active references.
- [x] Do not change Business schema fields or product task endpoints in this ticket.

## Unit Test Work

- [x] Run the new PR-110 guardrail test.
- [x] Run existing Runtime LLM prompt contract tests.

## Smoke Test Work

- [x] Run a Runtime import/compile smoke after deletion.
- [x] Confirm grep output has no active Runtime self-drive prompt modules outside the guardrail test.

## Deployment Work

- [x] Deploy Agent Runtime with `./deploy runtime`.
- [x] Confirm service status after deploy.

## GitHub / Commit Work

- [x] Commit the `novaic-agent-runtime` deletion and guardrail test.
- [x] Commit the parent repo submodule pointer and ticket update.
- [x] Push both commits.

## Closeout

Closed 2026-04-30.

Evidence:

- `rg` confirmed the deleted modules had no active external imports before removal.
- `python -m pytest tests/test_pr110_retired_self_drive_cleanup.py tests/test_llm_prompt_contract.py` passed.
- `python -m compileall -q task_queue` passed.
- `rg` over `novaic-agent-runtime/task_queue` found no active references to the retired modules or old self-drive prompt phrases.
- `./deploy runtime` passed and restarted backend services.
- Remote verification on `api.gradievo.com` confirmed all four retired files are deleted.
