# Classify task queue production residue hits

## Problem Definition

P538 must classify every static-residue production hit under `novaic-agent-runtime/task_queue` from P531. The classification has to be complete enough to decide whether the hits are expected live architecture surface, harmless documentation/test-adjacent wording, or risky old logic that needs a follow-up.

## Proposed Solution

Use the P531 production scan output as the source of truth, filter it to `novaic-agent-runtime/task_queue`, count hits by file, and write a classification table. For each production file, record the hit count, matched terms, category, rationale, and whether a follow-up is needed. Keep the output pointer-sized: artifacts contain the raw filtered lines and counts, while the result summarizes the classification.

## Acceptance Criteria

- The task queue production hit count is reconciled against P531 production output.
- Every `novaic-agent-runtime/task_queue` production file with a hit is represented exactly once in the classification table.
- Each file has a category and rationale tied to the matched terms.
- Any risky compatibility, fallback, direct publish, or old imperative branch residue is identified as follow-up-worthy.
- Counts and artifact paths are recorded for later P534/P532 reconciliation.

## Verification Plan

Compare the filtered hit count against file-count totals, verify table row count equals the number of unique task queue production files, and stress-check the classification for hidden compatibility/fallback semantics rather than accepting benign-looking names at face value.

## Risks

- A keyword hit such as `optional`, `publish`, or `remaining_stack` may look suspicious but be a current explicit contract rather than residue.
- Conversely, a hit can be a real risk if it reflects bypassing FSM/outbox boundaries or preserving a legacy path.
- Documentation strings can inflate counts and should not be mixed with live behavior without an explicit classification.

## Assumptions

- P531 scan artifacts remain the canonical input for this classification.
- P539 will reconcile this task_queue classification with the already completed queue_service classification.
