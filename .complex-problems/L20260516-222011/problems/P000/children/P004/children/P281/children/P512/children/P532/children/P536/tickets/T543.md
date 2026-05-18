# Reconcile full static residue classification

## Problem Definition

P536 must reconcile the production and test residue classifications back to P531's raw static scan totals. It proves the classification phase did not lose any hits and that risky residue is either absent or closed.

## Proposed Solution

Compare P534 production classification and P535 test classification against P531 totals. Record arithmetic, file ownership counts, risk status, and the only code cleanup performed during this audit.

## Acceptance Criteria

- Production + test classified hit counts equal P531 raw hit count.
- Production + test classified file counts equal P531 raw file count.
- Risky residue is absent or linked to closed follow-up.
- A durable reconciliation artifact is written for P532.

## Verification Plan

Use P531 count artifact, P534 production closure, and P535 test closure. Fail if counts mismatch or any risky child residue remains open.

## Risks

- P540 changed code after P531 scan; reconciliation must distinguish original scan classification from current post-fix state.

## Assumptions

- P534 and P535 are the complete split children for static residue classification.
