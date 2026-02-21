# Round 008 Canonical repo_url Audit

## Metadata
- generated_at: `2026-02-21T03:24:59Z`
- report_snapshot_sha: `51a11b116524e56f`

## Fix notes (carried forward from R007)
- removed overly strict slash-count heuristic for `file:///` paths
- _normalise_url() strips nested-list `- ` prefix and backticks

- reports_scanned: `7`
- failures: `0`

## Failures
- none

## Marker
- `ROUND008_CANONICAL_REPO_URL_AUDIT_COMPLETED`