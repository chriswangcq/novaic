# Service code semantic residue discovery check

## Summary

Success. Result R749 solves P753 because all split service-code discovery children are closed, the findings distinguish intentional protocol code from stale residue, exact remediation candidates are listed, and no product code was modified in this discovery branch.

## Evidence

- R749 cites R737, R738, R742, and R748.
- P755, P756, and P757 are done and have success checks.
- R749 aggregates remediation candidates across Runtime/Cortex, Business/Device, LogicalFS, Sandbox, VMuse, and app resource copies.

## Criteria Map

- Criterion: Focused scans cover service source directories and tests without bulk-loading large generated files.
  Evidence: R737 covers Runtime/Queue/Cortex; R738 and R742 cover Gateway/Business/Device source/tests; R748 covers Blob/LogicalFS/Sandbox/VMuse/app resource copies.
- Criterion: Findings classify active stale code/comments versus intentional protocol code, auth encoders, tests, or fixtures.
  Evidence: R737-R748 each classify current protocol/guardrail hits separately from stale residue.
- Criterion: Exact safe code remediation candidates are listed.
  Evidence: R749 Known Gaps lists precise files and cleanup targets.
- Criterion: No code is modified in this discovery child.
  Evidence: R749 Known Gaps states no product code was modified.

## Execution Map

- T745 was classified split because service-code residue spans independent ownership layers.
- Split children P755, P756, and P757 completed discovery and verification.
- P756 created and closed follow-up P758 for tests before final success.
- Parent result R749 aggregated child results.

## Stress Test

- Plausible failure mode: direct/base64/media terms could trigger broad over-deletion.
- Check result: child results explicitly preserve intentional auth/wire/media protocol usage and only list precise stale or misleading paths.
- Plausible failure mode: generated app copies could keep old VMuse media behavior after source cleanup.
- Check result: P757/P766 identified copied app resources as separate remediation targets.

## Residual Risk

- Medium but non-blocking for P753. Discovery is solved; the next remediation branch must apply and test the listed changes.

## Result IDs

- R749
