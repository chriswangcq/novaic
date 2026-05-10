# Phase 3D File-Walk Stack Quarantine And Deletion

## Problem Definition

After Phase 3C, the primary runtime control paths for `context_status`, `skill_begin`, and `skill_end` use SQLite active-stack projection, but `novaic-cortex/novaic_cortex/api.py` still contains file-walk stack reads through `_collect_active_stack` and path routing through `resolve_active_scope_path`.

This phase must make the remaining file-walk usage explicit and non-authoritative. Runtime stack authority must not be split between SQLite projection and filesystem scanning. Any remaining filesystem stack traversal must either be deleted or renamed/documented as repair/debug-only, with tests and static guards preventing it from returning to live authority paths.

## Proposed Solution

Perform a bounded quarantine/deletion pass over the remaining stack file-walk surfaces:

- Audit every remaining `_collect_active_stack(...)` and `resolve_active_scope_path(...)` call in `novaic-cortex/novaic_cortex/api.py`.
- Replace runtime response/error/diagnostic stack contexts with `read_active_stack_projection(...)` where the response needs current stack shape.
- Delete obsolete post-create projection seeding that re-derives stack state from file-walk after successful `skill_begin`; projection writes should be computed from the already-read SQLite frames plus the new child frame.
- Replace archive/finalize remaining-stack snapshots with SQLite projection-derived frames where possible, so finalize events are not based on file-walk authority.
- For non-stack routing endpoints that still need an active scope path, either cut them to SQLite `active_scope_path` or isolate them behind explicitly named repair/debug helpers if they are not runtime authority.
- Rename or remove `_collect_active_stack` if no live runtime code should call it. If retained, give it a repair/debug name and keep it out of primary API control paths.
- Add/strengthen tests and static guards:
  - no `_collect_active_stack` in `context_status`, `skill_begin`, `skill_end`;
  - no `resolve_active_scope_path` in stack-authority decisions;
  - wrong-scope, empty-stack, duplicate-begin, depth-limit, archive/finalize, and tool/write routing behavior still preserve API semantics.

## Acceptance Criteria

- Every remaining `_collect_active_stack` use is either removed or explicitly classified as repair/debug-only by name and guard.
- `skill_begin`, `skill_end`, and default `context_status` do not use file-walk stack collection in success, error, or exception response authority.
- Scope archive/finalize remaining-stack event data comes from SQLite active-stack projection rather than file-walk stack snapshots.
- Post-`skill_begin` active-stack projection updates do not re-read from file-walk.
- Active-path routing endpoints are explicitly reviewed and either migrated to SQLite projection or documented as non-stack file routing outside this phase.
- Tests and grep/static guards fail if file-walk authority is reintroduced into live stack control paths.

## Verification Plan

- Run a static audit:
  - `rg -n "_collect_active_stack\\(|resolve_active_scope_path\\(|read_active_stack_projection\\(" novaic-cortex/novaic_cortex/api.py -S`
  - section-level checks for `context_status`, `skill_begin`, `skill_end`, archive/finalize paths, and routing endpoints.
- Run targeted Cortex tests covering:
  - active-stack projection helper;
  - skill lifecycle begin/end;
  - control-stack mismatch/empty-stack behavior;
  - status API stack output;
  - archive/finalize stack projection behavior;
  - static read-source guards.
- Run the full Cortex test suite:
  - `PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q novaic-cortex/tests`
- If the audit reveals multiple independent residue clusters, split this ticket into child problems instead of doing a broad one-go change.

## Risks

- Archive/finalize code may rely on historical file layout details; replacing it with projection-derived frames could expose missing projection data for old tests or synthetic workspaces.
- Some routing endpoints may use active scope paths for file IO rather than stack authority; migrating them blindly could widen scope. They must be classified before deletion.
- Exception diagnostics can look harmless but still carry old authority assumptions into future code. They should be cut to SQLite or made explicitly non-authoritative.

## Assumptions

- Phase 3C has already established SQLite active-stack projection as the runtime stack authority for `context_status`, `skill_begin`, and `skill_end`.
- Operational SQLite store is available in API paths where active-stack projection is read or written.
- Backward compatibility with old file-walk authority is not required; the user explicitly prefers deleting old code over maintaining fallback paths.
