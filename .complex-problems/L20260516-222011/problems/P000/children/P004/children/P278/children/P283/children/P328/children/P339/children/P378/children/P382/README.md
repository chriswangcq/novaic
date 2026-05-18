# Runtime finalize source guard classification

## Problem

Runtime source must be scanned for stale finalize/session-ended compatibility residue that tests might not exercise: unsafe generation coercion, missing generation defaults, direct active clears, and current-active fallback behavior.

## Success Criteria

- Runtime source guards are run over `queue_service`, `task_queue`, and relevant tests.
- Every guard hit is classified as safe, fixed, or moved into a follow-up problem.
- No live runtime path remains that can clear, restart, or archive a newer active session from stale/missing generation.
- The result includes file-level evidence for the classification.
