# Round 008 Gate Criteria

## Gate A - Canonical URL Closure
- `canonical-repo-url-audit.md` reports zero failures.
- `local:` repo URL scheme is absent in all report artifacts.

## Gate B - Audit Freshness and Correctness
- Cross-team and format audits are generated after final report updates.
- Audit outputs include run timestamp and report snapshot reference.

## Gate C - Evidence and Marker Quality
- Required PASS markers are explicit and machine-greppable.
- No template placeholders in report fields.
- Each team includes at least one failure-path replay with deterministic marker.

## Gate D - Communication Clarity
- Every team report has `questions_for_program_owner` section.
- Questions use structured fields: `question`, `why_blocking`, `options`, `recommended_option`.
- Each team report includes one operability artifact path (`runbook`, `smoke script`, or `replay bundle`).

## Fail Conditions
- any canonical URL failure remains
- stale audit artifact (older than report updates)
- missing `questions_for_program_owner` section
- missing failure-path replay evidence
