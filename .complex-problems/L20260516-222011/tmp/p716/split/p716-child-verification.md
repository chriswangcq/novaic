# Business/subscriber boundary verification sweep

## Problem

Run focused scans and relevant lints/tests after Business/subscriber remediation children close, proving active residue is gone or intentionally retained. This belongs under P716 because remediation without a final verification sweep risks leaving stale or unconnected changes.

## Success Criteria

- Focused `rg` scans cover Business/subscriber boundary terms across code, docs, scripts, and launch surfaces.
- Relevant architecture/status lint or boundary guard commands are run and reported.
- If source code changed, a narrow test/import/compile check is run where practical.
- Residual matches are classified as intentional current docs, historical comparison, test-only, or follow-up; none are unexamined active stale claims.
