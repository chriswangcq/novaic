# Worker and health counter classification ticket

## Problem Definition

Worker and health files contain retry/count/status numeric defaults. They must be classified so final compatibility checks can distinguish worker metrics from session-generation authority.

## Proposed Solution

Inspect worker/health hits from P402, classify them as counters/status/retry metadata or patch any session mutation path if discovered.

## Acceptance Criteria

- Worker and health hits are classified.
- No worker counter path writes attach/finalize/session-ended generation authority.
- Relevant worker tests pass.

## Verification Plan

- Run targeted guard over task worker, task execution, health action specs, and worker tests.
- Run focused worker/health tests.

## Risks

- Counter defaults are expected; do not overfit guard cleanup by deleting useful metrics.

## Assumptions

- Worker counters are not session-generation authority unless they feed session mutation code directly.
