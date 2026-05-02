# PR-186A — Runtime Wake Observation / Reply Lifecycle Acceptance

Status: `[closed]` — 2026-05-03

## Analysis

Runtime already has focused tests for:

- `session.init` forwarding trigger notification ids into Cortex scope meta and claiming them.
- `context.read` rendering notification hints only.
- Environment IM executors, including `im_reply` blocked before `im_read`.
- `scope_end` marking claimed notifications processed only after successful archive.

The gap is a single acceptance-level guard that reads these as one architecture contract.

## Scope

- Add Runtime acceptance tests binding the sequence:
  `session.init` → notification-only context → `im_read` checkpoint → `im_reply` → `scope_end` processed.
- Guard that no raw message body enters prompt context before observation.
- Guard that `im_reply` remains fail-closed if the observation checkpoint is missing.

## Tests

- Runtime targeted pytest for the new acceptance file.
- Runtime full pytest before closure.

## Deployment / Git

- If only tests/docs change: no service deploy required.
- If runtime behavior changes: deploy Runtime and record smoke evidence.

## Closure

- Added `tests/test_pr186_runtime_main_path_acceptance.py`.
- Covered notification-only prompt hints, `im_reply` fail-closed before `im_read`, observation checkpointing, successful reply execution, and scope-end processed transition after archive.
- Tests:
  - `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr186_runtime_main_path_acceptance.py` → `2 passed`
  - `PYTHONPATH=.:../novaic-common pytest -q` → `176 passed`
- No Runtime deploy required; no behavior changed.
