# Verify Active Stack SQLite Authority Cutover

## Problem Definition

Phase 3 implemented active-stack projection writes, runtime read cutover, and file-walk authority deletion across P018-P020. This final gate must prove the aggregate state is coherent: SQLite is the active-stack authority, old runtime file-walk paths are gone, restart/reopened Workspace behavior works, and remaining file projection code is not runtime stack authority.

## Proposed Solution

Run a strict verification pass rather than new feature work:

- Run targeted tests covering active-stack helpers, skill lifecycle nesting, mismatch, empty-stack, archive/finalize, restart/reopened Workspace behavior, status reads, assistant/step routing, and static guards.
- Run static residue searches for `_collect_active_stack`, `resolve_active_scope_path`, `read_step_index` stack-walk patterns, and active-stack projection read/write calls in `api.py`.
- Run `py_compile` for `novaic-cortex/novaic_cortex`.
- Run the full Cortex test suite.
- Record any discovered gap as follow-up rather than papering over it.

## Acceptance Criteria

- Targeted verification tests pass for nesting, mismatch, finalize/open-child behavior, restart recovery, status reads, and active write routing.
- Static residue search proves `api.py` has no `_collect_active_stack` or `resolve_active_scope_path` runtime authority.
- Static review identifies any remaining stack-related file projection code and classifies it as non-runtime trace/repair/debug or opens a follow-up.
- `py_compile` passes for `novaic-cortex/novaic_cortex`.
- Full Cortex test suite passes.

## Verification Plan

- `PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q <targeted tests>`
- `PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q novaic-cortex/tests`
- `python3 -m py_compile $(find novaic-cortex/novaic_cortex -name '*.py' | sort)`
- Static `rg` audits over `api.py`, `workspace.py`, and tests.

## Risks

- Static residue can include lower-level repair/debug helpers outside live `api.py`; the check must distinguish runtime authority from non-runtime support code.
- If verification finds a real gap, this ticket should record that result and let problem-level check create a follow-up.

## Assumptions

- Phase 3E is a verification gate; any non-trivial implementation gap discovered here should become a follow-up problem rather than being silently folded into the check.
