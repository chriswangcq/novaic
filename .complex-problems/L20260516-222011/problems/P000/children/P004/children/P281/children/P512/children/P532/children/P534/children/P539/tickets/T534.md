# Reconcile production residue classifications

## Problem Definition

P539 must reconcile the two production classification children under P534: queue_service production hits and task_queue production hits. The reconciliation must prove that their combined classified counts equal the P531 production hit count and that no risky production residue remains unhandled.

## Proposed Solution

Read P531 production counts, P537 queue_service classification artifacts, and P538/P540 task_queue classification and cleanup artifacts. Produce a reconciliation table with per-area counts, classified file counts, risky-residue status, and evidence paths. Record whether the production side of the static residue audit is closed.

## Acceptance Criteria

- Combined classified production hit count equals P531 production total.
- Combined classified production file count equals P531 production file count.
- Queue_service and task_queue classifications are both represented.
- Any risky production residue is either absent or linked to a closed follow-up.
- A durable reconciliation artifact is written for P534.

## Verification Plan

Compute counts directly from P531 scan artifacts and compare them to P537/P538 classification counts. Verify P540 closed the task_queue optional-step follow-up. Fail the check if counts do not reconcile or if a risky production residue remains open.

## Risks

- Parent totals can look correct while one production file remains unclassified.
- P538 initially found risk, so reconciliation must include P540 closure rather than treating R526 alone as sufficient.

## Assumptions

- P537 and P538 are the complete split children for P534 production classification.
