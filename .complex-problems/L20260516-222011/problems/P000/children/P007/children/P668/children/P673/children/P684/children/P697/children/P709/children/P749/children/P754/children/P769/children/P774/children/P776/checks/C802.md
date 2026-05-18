# App factory logs page and detail discovery check

## Summary

Success. R756 satisfies the discovery problem: it located the real factory logs UI, classified backend/list/detail behavior, and named exact remediation candidates. The one-go execution is acceptable because this child was discovery-only, scoped to one externally deployed static page plus its route/contract tests, and produced concrete file/line evidence.

## Evidence

- R756 identifies `novaic-llm-factory/static/factory-logs.html` as the actual Factory Logs page rather than assuming it lives in `novaic-app/src`.
- `.complex-problems/L20260516-222011/tmp/p776-factory-log-scan.txt` records bounded source discovery.
- `.complex-problems/L20260516-222011/tmp/p776-factory-log-evidence.txt` records the high-signal static page, backend route, contract, and test evidence.
- `novaic-llm-factory/factory/routes/log_routes.py` omits bodies from list results and bounds detail bodies.
- `novaic-llm-factory/factory/contracts.py` redacts provider-native request media data.
- `novaic-llm-factory/static/factory-logs.html` visual and raw detail renderers still lack binary/media/_mcp_content scrubbing, so exact remediation candidates are present.

## Criteria Map

- Factory-log page, hook/service, table, detail modal, and API-client files discovered: satisfied; the scan found the static page and backend API route, and also proved there is no equivalent `novaic-app/src` factory-log page.
- Hits for request body, response body, raw JSON, `_mcp_content`, base64, BlobRefs, artifacts, display results, and truncation classified: satisfied by R756 Verification and Known Gaps.
- Exact remediation candidates listed: satisfied; R756 names static page visual/raw renderers and missing guard tests.
- No factory-log UI files modified: satisfied; this was read-only discovery.

## Execution Map

- T767 was classified as `one_go`, moved to execution, and produced R756.
- The discovery widened from `novaic-app/src` to repo-level only after evidence showed the UI was not in the app frontend; this is appropriate because the user-visible factory logs page is a deployed static asset in `novaic-llm-factory`.
- No follow-up is needed at this child level; remediation belongs to a later parent/follow-up implementation ticket.

## Stress Test

- Plausible failure mode: the page could look fixed because the backend truncates bodies, while still showing the first 20,000 chars of base64 or `_mcp_content`. R756 explicitly checks the static renderers and records that truncation is not scrubbing.
- Plausible false negative: the main app might have another factory-log UI. The scan found none under `novaic-app/src` and located docs/deploy references to the static factory page instead.

## Residual Risk

- Non-blocking for discovery: no browser/runtime test was run against the live page in this child. Source evidence is enough to list remediation candidates, and live verification should happen after implementation.
- Non-blocking for discovery: old historical logs may still contain raw payloads even after future UI scrubbing; remediation should focus on display safety and contract tests.

## Result IDs

- R756
