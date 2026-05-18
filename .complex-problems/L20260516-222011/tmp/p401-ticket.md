# Widened guard matrix ticket

## Problem Definition

After the live `event_generation` and subagent wake `session_generation` fixes, the widened guard must be rerun and every remaining generation-like/default hit must be classified. This closes the last ambiguity from P398/P389.

## Proposed Solution

Run narrow and widened guards, inspect every remaining hit, classify each as live session authority, event sequencing, round number, retry/health counter, persistence/audit adapter, or generic non-session counter. Patch only if the matrix finds another live authority/default issue; otherwise record the matrix and focused test evidence.

## Acceptance Criteria

- Narrow session-generation guard is clean.
- Widened guard output is fully classified with file evidence.
- No unclassified live session-generation or event-generation residue remains.
- Any newly discovered live authority hit is patched and tested.
- Focused runtime tests pass.

## Verification Plan

- Run narrow guard.
- Run widened guard.
- Inspect relevant files and build a matrix.
- Patch if needed.
- Run focused runtime tests and guards again.

## Risks

- Misclassifying a live path as a harmless counter would reintroduce hidden stale-session behavior.
- Over-fixing counters would add maintenance noise.

## Assumptions

- Round numbers, retry counters, and health counters are acceptable only if they do not participate in session generation authority.
