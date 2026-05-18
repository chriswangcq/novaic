# Ticket: Audit session compatibility and legacy residue

## Problem Definition

Search for legacy session compatibility branches, old active-session APIs, direct saga creation bypasses, hidden env/global inputs, and duplicate worker/session configuration that could keep old logic alive after the FSM/session-outbox migration.

## Proposed Solution

- Run source guards for:
  - legacy/compat/fallback names
  - old active session APIs/tables
  - direct saga creation and session side-effect bypasses
  - env/global hidden inputs in session coordinator/worker paths
  - duplicate worker/session config paths
- Classify retained hits as required active path, safe guard/docs, risky branch, or removable residue.
- Fix small removable residue directly; split risky branches into follow-up problems.

## Acceptance Criteria

- Guard artifacts are saved.
- Every retained category is classified.
- Risky/removable residue is fixed or followed up.

## Verification Plan

- `rg` guards over `novaic-agent-runtime/queue_service`, `task_queue`, and tests.
- Focused tests if source cleanup is performed.
