# Ticket: Patch active Cortex boundary residue

## Problem Definition
Active scripts/docs still contain wording that may imply Cortex owns Sandboxd process execution or foundational file authority. Patch the safe active candidates from P711 and verify the wording now reflects Cortex semantic/context/shell orchestration boundaries.

## Proposed Solution
Patch the bounded active candidates in `scripts/start.sh`, `docs/architecture/service-topology.md`, and `docs/cortex-architecture.md`. Inspect the intentional contrast row around `docs/architecture/service-topology.md:131` and patch only if still misleading.

## Acceptance Criteria
- `scripts/start.sh` describes Cortex without claiming Sandbox ownership.
- `docs/architecture/service-topology.md` Cortex row distinguishes payload manifest/shell orchestration from sandbox execution.
- `docs/cortex-architecture.md` distinguishes Workspace semantics and shell/sandbox orchestration from foundational file/sandbox ownership.
- Focused scans show no touched active surface still has the retired misleading phrases.
- Relevant boundary lint passes.

## Verification Plan
Use `apply_patch` for the bounded edits, run focused `rg` scans over the touched active files, and run `python3 scripts/ci/lint_blob_workspace_boundary.py`.
