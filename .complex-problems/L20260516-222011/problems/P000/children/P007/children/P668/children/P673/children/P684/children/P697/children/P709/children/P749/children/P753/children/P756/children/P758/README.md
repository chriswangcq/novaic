# Gateway Business Device test residue discovery

## Problem

P756 found useful Gateway, Business, and Device source-code residue candidates, but did not provide evidence that relevant tests were scanned. The remaining gap is to scan relevant test files for stale Gateway/Business/Device ownership, old media/control route, direct/fallback/compatibility, and screenshot/base64 residue, then classify any hits as intentional guard fixtures, current protocol tests, or remediation candidates.

## Success Criteria

- Relevant tests under `novaic-gateway`, `novaic-business`, and `novaic-device` are searched with bounded, reproducible commands.
- Test hits are classified separately from production code hits.
- Any stale or misleading active test fixture/comment is listed as a remediation candidate.
- No product code is modified in this discovery follow-up.
