# Session hidden input and duplicate config audit ticket

## Problem Definition

P466 must prove that the session/worker coordination path no longer relies on hidden environment reads, global runtime state, or duplicate configuration branches that can keep retired logic alive. Unlike P465, this problem includes remediation if risky hidden inputs are found.

## Proposed Solution

Split the work into narrower child problems: first inventory hidden inputs and duplicate config surfaces, then classify risky hits, then fix or explicitly close each retained hit with tests. The audit must cover `queue_service`, `task_queue`, subscriber/dispatcher setup, and relevant tests. Any production hidden input used inside a decision path should be removed or injected through an explicit boundary.

## Acceptance Criteria

- Source guards cover implicit `os.environ`, `getenv`, module globals, singleton/default configuration, and duplicate config branching in session/worker paths.
- Retained hits are classified as safe adapter-boundary reads, test-only fixtures, or risky production hidden inputs.
- Risky production hidden inputs are fixed directly in child work or split further into smaller fix problems.
- Tests or guard checks prove fixed paths are deterministic from explicit inputs.

## Verification Plan

Run targeted `rg` guards and focused pytest suites for session repository/FSM/outbox/worker configuration. Review source slices around each retained hit. The final check must cite both guard artifacts and focused tests.

## Risks

- Environment reads at true process-boundary configuration may be valid and should not be blindly removed.
- Hidden input may exist under new names that simple keyword guards miss.
- Fixes can accidentally widen constructors or config plumbing if not kept at explicit dependency boundaries.

## Assumptions

- This problem is broad enough to split before execution.
- The user prefers eliminating compatibility branches over preserving old behavior.
