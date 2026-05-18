# Business/subscriber cleanup candidate disposition

## Problem

Review the cleanup candidates from P715 and classify each as active stale claim, intentional historical/current comparison, test-only fixture, already-clean code path, or follow-up-worthy broad cleanup. This belongs under P716 because remediation should not patch blindly without first separating active residue from intentional references.

## Success Criteria

- P715 cleanup candidates are enumerated and classified.
- `docs/entangled-architecture.md` Gateway/Business CRUD wording receives an explicit disposition.
- Launch/docs scan hits that mention Business/subscriber plus Queue/Runtime/Cortex/Gateway/Device/Entangled are sampled enough to justify the remediation scope.
- Any candidate that is too broad for safe direct patching is named as a follow-up candidate rather than ignored.
