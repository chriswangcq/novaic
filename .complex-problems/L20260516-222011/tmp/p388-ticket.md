# Produce final cross-repo generation residue guard matrix

## Problem Definition

After runtime and Cortex targeted patches, the parent problem still needs a skeptical final guard matrix proving no unclassified live generation/default/finalize compatibility residue remains.

## Proposed Solution

Rerun the cross-repo generation coercion, active-session, finalize/archive, and legacy compatibility guards across the target runtime and Cortex directories. Classify every hit as fixed, safe helper/test code, safe adapter boundary, or residual follow-up.

## Acceptance Criteria

- Generation coercion guard has no unclassified live matches.
- Active-session/current-active guard hits are classified and do not reveal stale active-session mutation risks.
- Finalize/archive/remaining-stack guard hits are classified and do not reveal deprecated uncontrolled finalize branches.
- Result contains a concise matrix with file evidence and command outcomes.

## Verification Plan

Run the guard `rg` commands used in P380/P385, inspect each hit, and record a matrix rather than changing code.

## Risks

- Guard keywords may intentionally match safe helper code or tests; classification must distinguish evidence from residue.

## Assumptions

- Any new live residue found here should be reported as a known gap for follow-up rather than patched inside this guard-only ticket.
