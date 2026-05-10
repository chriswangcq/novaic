# Extract shell capability, LogicalFS, and process execution modules

## Problem Definition

The public shell path is physically concentrated in `novaic_cortex/sandbox.py`, making unrelated responsibilities look coupled.

## Proposed Solution

Move shell capability CLI generation to `shell_capabilities.py`, LogicalFS/view/mount/path helpers to `logical_fs.py`, and generic process execution to `sandbox_exec.py`. Keep `sandbox.py` as a small facade/orchestrator importing those components. Keep compatibility re-exports only for existing tests and only when they point at the canonical module implementation.

## Acceptance Criteria

- `sandbox.py` no longer contains the large capability script.
- `sandbox.py` no longer contains `MountNamespaceLogicalFS` implementation.
- `sandbox.py` no longer contains `SandboxExec` implementation.
- Existing public import `Sandbox` remains unchanged.
- Behavior stays unchanged, including no local fallback.

## Verification Plan

- Run compile/import checks.
- Run targeted sandbox/logicalfs/capability tests after extraction.
- Run residue scan for duplicated class/function definitions.

## Risks

- Mechanical extraction may miss imports or test monkeypatch targets.
- Private helper tests may need to import from the new canonical module.

## Assumptions

- Re-exporting selected helpers from `sandbox.py` is acceptable only as a compatibility surface, not as a second implementation.
