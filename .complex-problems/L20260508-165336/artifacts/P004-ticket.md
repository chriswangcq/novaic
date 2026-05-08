# Ticket: Summarize Pure DSL Remediation Backlog

## Problem Definition

P001 proved the new runtime/FSM path is live. P002 proved the system is not pure DSL yet. P003 proved old active legacy branches were not found but guard hygiene needs tightening. We need a concrete, ordered implementation backlog that can be turned into future tickets without losing the design intent.

## Proposed Solution

Synthesize P001-P003 into a remediation roadmap. Each backlog item must name the target files, the intended end state, deletion/cleanup expectations, and the guard/test needed to prevent partial cutover.

## Acceptance Criteria

- Produce an ordered set of future implementation tickets for closing the pure DSL gap.
- Include both implementation and old-code deletion/guard work.
- Include file-level targets and measurable acceptance criteria for each item.
- Explicitly state what is already done and should not be reworked.
- Avoid making code changes in this audit ticket.

## Verification Plan

- Read P001/P002/P003 results and checks.
- Cross-reference the current source evidence gathered in those results.
- Record a backlog result with ticket-sized items and sequencing.

## Risks

- The backlog could become vague architecture prose unless each item has file targets and success checks.
- A single oversized “make pure DSL” item would repeat the earlier problem of writing new code without deleting old paths.

## Assumptions

- Future implementation should follow the user’s principles: code generation is cheap, branch maintenance is expensive, and misleading residue is harmful.
