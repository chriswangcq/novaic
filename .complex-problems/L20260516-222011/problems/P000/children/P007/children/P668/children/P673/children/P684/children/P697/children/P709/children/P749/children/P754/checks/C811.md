# Check P754 App Resource And Generated Asset Semantic Residue Discovery

## Summary
`P754` succeeds as a discovery problem. It covered the app resource/generated asset areas relevant to VMuse, Device, display, and shell tooling; separated source-of-truth paths from copied/generated paths; and produced concrete remediation candidates without manually changing generated assets.

## Evidence
- `R750` covers VMuse copied resource trees and identifies synchronized copy paths that mirror stale source behavior.
- `R754` covers Tauri backend scripts/resources, VmControl launch wiring, backend binary/resource packaging, and the stale HD tools comment.
- `R764` covers App frontend/Monitor output contracts, including Factory Logs raw detail UI, Chat message parsing, BlobRef preview, ActivityTimeline projection, unused `SmartValue`, and legacy `AssistantMessage` event rendering.
- `R765` aggregates the child findings and lists implementation gaps explicitly.

## Criteria Map
- `scans cover novaic-app resource and generated asset locations relevant to VMuse, Device, display, and shell tooling`: success.
- `findings distinguish generated copies from source-of-truth code/docs`: success.
- `required sync/remediation candidates are listed for remediation child`: success.
- `no generated assets manually patched in discovery child`: success.

## Execution Map
- Reviewed child result summaries and the aggregated parent result.
- Checked that the parent result names remediation candidates rather than claiming implementation is done.

## Stress Test
- If the standard were “all candidates are already fixed,” this would fail, but that is not the stated scope of `P754`; this problem is specifically discovery.
- The riskiest gap is generated asset synchronization. The result preserves that boundary by requiring source cleanup plus synchronized copy/generated updates later.
- The App frontend active paths have passing tests in child checks, but residue remains in unused or inactive paths; the result does not hide that.

## Residual Risk
- Implementation tickets must still execute the cleanup list and run focused tests.
- Generated asset policy should be respected during remediation to avoid manual divergence.

## Result IDs
- Checked result: `R765`.
- Supporting results: `R750`, `R754`, `R764`.
