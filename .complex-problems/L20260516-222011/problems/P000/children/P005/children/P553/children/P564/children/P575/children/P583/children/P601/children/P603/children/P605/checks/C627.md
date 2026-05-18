# P605 exact backend preview boundary check

## Summary

P605 succeeds. R589 closes the P603 evidence gap by adding exact backend slices, targeted raw-bytes risk scanning, and focused test output. The evidence supports that Agent Monitor/progress preview paths use bounded text/reference contracts and are separate from the LLM display-perception image injection path.

## Evidence

- Exact line-numbered evidence artifact: `.complex-problems/L20260516-222011/tmp/p605-exact-backend-preview-evidence.txt`.
- Raw bytes risk scan artifact: `.complex-problems/L20260516-222011/tmp/p605-raw-bytes-risk-scan.txt`.
- Focused test output artifact: `.complex-problems/L20260516-222011/tmp/p605-focused-tests.txt`.
- Focused tests passed: `8 passed in 0.35s`.

## Criteria Map

- Exact line-numbered slices for `/v1/steps/read_preview`, payload inspection APIs, payload externalization/indexing, and Business/runtime monitor projection surfaces: satisfied by `p605-exact-backend-preview-evidence.txt`.
- Focused tests for payload externalization, bounded payload preview/read APIs, and Agent Monitor timeline/progress boundary behavior: satisfied by `p605-focused-tests.txt`.
- Record whether backend monitor/progress events can carry raw image bytes/base64: satisfied by `p605-raw-bytes-risk-scan.txt` and R589, which found no such monitor/progress path.
- Map evidence back to original P603 criteria with residual risk: satisfied by R589 and this check.

## Execution Map

- The ticket captured backend slices with `nl -ba` for Cortex APIs, workspace step externalization, preview projection, Business schema, runtime activity projection, display image-ref resolution, and display handler boundaries.
- The ticket ran a targeted repository scan for `base64`, screenshot, `image_ref`, artifacts, payload references, progress, timeline, and monitor paths.
- The ticket ran 8 focused pytest cases across Cortex and Business.

## Stress Test

- The check specifically looked for the risky failure mode that caused the original issue: raw screenshot/base64 escaping into a durable or UI-visible path. The targeted scan found base64 producers, but the evidence classifies them as expected shell/device blob wrapping or explicit display-perception LLM image resolution, not Agent Monitor progress payloads.
- The test set includes both small payload references and large payload externalization to BlobRef, plus bounded read/search/summarize/QA behavior.

## Residual Risk

- This does not prove every future monitor feature will stay bounded. The remaining non-blocking risk is regression from future fields that bypass these projection helpers.
- There was no full browser Agent Monitor UI render test in this follow-up, but P605’s backend boundary scope is satisfied.

## Result IDs

- R589
