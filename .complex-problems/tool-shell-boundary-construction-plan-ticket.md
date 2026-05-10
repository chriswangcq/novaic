# Design phased construction plan for shell boundary migration

## Problem Definition

The previous design established the target tool boundary, but not the actual construction plan. The missing piece is a detailed, dependency-ordered plan that engineers/agents can execute later without accidentally adding new code while leaving old harness paths alive.

## Proposed Solution

Inspect the current Runtime/Cortex/Device/Business shape enough to map the migration to real modules. Then produce a phased construction plan with:

- phase goals and sequencing;
- concrete implementation tickets;
- touched modules/files;
- acceptance criteria;
- verification commands;
- cleanup/deletion gates;
- risk controls and rollback boundaries;
- final cutover criteria.

No production code changes should be made in this ticket.

## Acceptance Criteria

- The plan is concrete enough to execute as future tickets.
- The plan maps each phase to likely source modules and test surfaces.
- The plan explicitly prevents the anti-pattern "new path exists but old path still runs".
- The plan includes compatibility windows and mandatory physical deletion gates.
- The plan covers ToolOutputV1, artifact manifests, Cortex projection, shell capability substrate, display hardening, IM/subagent/device migration, monitor projection, and architecture guards.
- The plan records verification and residual risks.

## Verification Plan

- Compare the result against root success criteria.
- Verify the plan cites real existing source locations.
- Verify no runtime code changes were made.
- Validate/render the ledger.

## Risks

- The plan could become too broad; mitigate by breaking phases into crisp tickets.
- Real code may differ during later implementation; mitigate by including discovery gates at the start of each phase.
- Compatibility cleanup is easy to postpone; mitigate by making deletion gates phase acceptance criteria.

## Assumptions

- This is a design/plan turn only.
- Existing worktree may already contain unrelated modifications; do not revert or rely on them.
- Future implementation should follow the user's AI-era principle: code is cheap, branch residue and stale paths are expensive.
