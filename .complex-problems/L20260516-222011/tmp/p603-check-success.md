# P603 backend progress preview payload boundary final check

## Summary

P603 succeeds after follow-up R589. The original one-go result R588 found the relevant backend surfaces but was under-verified; R589 supplied exact line-numbered slices, raw-bytes risk scanning, and focused tests. Together they prove the backend Agent Monitor/progress preview boundary is bounded and reference-oriented, and that raw image/base64 handling is isolated from monitor progress payloads.

## Evidence

- R588: inventory scan artifact `.complex-problems/L20260516-222011/tmp/p603/backend-progress-preview-scan.txt`.
- R589: exact evidence artifact `.complex-problems/L20260516-222011/tmp/p605-exact-backend-preview-evidence.txt`.
- R589: raw bytes risk scan artifact `.complex-problems/L20260516-222011/tmp/p605-raw-bytes-risk-scan.txt`.
- R589: focused tests artifact `.complex-problems/L20260516-222011/tmp/p605-focused-tests.txt`.
- Focused tests passed: `8 passed in 0.35s`.

## Criteria Map

- Records exact scans for progress event, monitor event, step preview, and tool result payload creation: satisfied by R588 broad scan plus R589 exact `nl -ba` slices.
- Cites backend slices showing bounded preview or payload-ref/manifest behavior: satisfied by R589 slices for Cortex preview/payload APIs, workspace indexing, runtime activity projection, display image-ref resolution, and display handler boundaries.
- Separates backend monitor event payloads from LLM request context: satisfied by R589 evidence that monitor/activity projection uses summaries/payload flags, while provider-native image bytes are resolved only through explicit `display_perception` LLM projection.
- Creates a follow-up if backend monitor events carry raw image bytes: no raw monitor/progress path was found; the created follow-up was for evidence insufficiency and is now closed.

## Execution Map

- T595 performed initial backend scan and recorded gaps.
- C626 correctly rejected the one-go result due to insufficient slices/tests.
- T596/P605 collected exact evidence, ran focused tests, and recorded raw-bytes risk classification.
- C627 accepted P605.

## Stress Test

- The audit explicitly searched for `base64`, screenshot, `image_ref`, artifacts, payload refs, monitor, timeline, and progress paths outside tests. The risky base64 producers were classified as shell/device blob wrapping or display-perception LLM image resolution, not Agent Monitor progress payload emission.
- Focused tests cover large payload externalization, bounded payload reads/searches, redacted bounded summarize/QA inputs, and absence of old Agent Monitor timeline action hot paths.

## Residual Risk

- No blocking risk remains for current backend monitor/progress payload boundaries.
- Non-blocking future risk: new monitor fields could bypass the bounded projection helpers unless tests are extended when adding new monitor payload surfaces.

## Result IDs

- R588
- R589
