# Align Static Residue Guard Command Ticket

## Problem Definition

The static residue guard taxonomy and proposed scan command disagree. The command must include every listed term family before it can be used by P512.

## Proposed Solution

Update the guard design command to include missing taxonomy terms, regenerate the preview artifact with the corrected path set, and record the aligned command.

## Acceptance Criteria

- Proposed scan command includes `active_session`, `SessionDecision`, and `optional` in addition to the previous terms.
- Preview command runs without path errors.
- Result records corrected artifact paths.

## Verification Plan

- Inspect the updated guard design.
- Run the preview command and confirm it exits successfully.

## Risks

- Adding broader terms increases scan noise; P512 must classify rather than delete blindly.

## Assumptions

- This follow-up only corrects guard design artifacts, not production code.
