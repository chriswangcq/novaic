# Ticket: Produce aggregate compatibility final matrix

## Problem Definition

After the final guard matrix and focused behavior tests, produce the final aggregate compatibility matrix. The matrix must cover attach, finalize, session-ended, recovery, archive, context, shell, display, and payload categories, and state whether any dangerous compatibility residue remains.

## Proposed Solution

- Read P453 result/check for source/test guard classification.
- Read P454/P456/P457 results/checks for focused runtime and Cortex behavior verification.
- Synthesize a final category matrix:
  - attach / generation
  - finalize / remaining stack
  - session-ended / notifications
  - suspected-dead / recovery
  - archive / scope lifecycle
  - context projection / LLM prepare
  - shell output
  - display / current-turn perception
  - payload / blob / base64 boundary
  - tests / fixture residue
- If any dangerous unresolved residue is found, create a follow-up instead of marking success.

## Acceptance Criteria

- Final matrix is saved as a result artifact.
- Matrix cites P453/P454 child evidence.
- Result states whether unresolved dangerous residue remains.
- Any gap is routed into a follow-up.

## Verification Plan

- Cross-check matrix categories against P455 success criteria.
- Confirm every category has both scan classification or behavior-test evidence.
