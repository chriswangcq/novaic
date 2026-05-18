# PR-208 — Current Documentation Drift Cleanup

| Field | Value |
| --- | --- |
| Status | closed |
| Scope | Parent repo docs only |
| Goal | Remove misleading current-document wording that could revive old Gateway/outbox/continuity mental models. |

## Current State

Several current docs were mostly correct but still contained old implementation
phrases:

- roadmap entry points treated `technical-debt.md` like a live backlog;
- Gateway decomposition text still carried historical TODOs;
- Message/Wake status docs still described the old outbox-driven path;
- backend optimization recommendations described the April outbox-era main path.
- oclow knowledge pages still had stale tool lists and subscriber/outbox wording.

Historical PR ticket bodies remain useful archaeology and were not rewritten
wholesale.

## Small Tickets

### T1 — Clarify backlog/document entry points

- Objective: make `docs/README.md` and `technical-debt.md` point to current ticket SSOT.
- Scope: parent docs only.
- Expected result: `technical-debt.md` is clearly a historical ledger.
- Verification: grep/read docs entry sections.

### T2 — Archive Gateway decomposition text

- Objective: remove live TODO wording from the Gateway decomposition roadmap.
- Scope: `docs/architecture/gateway-decomposition-roadmap.md`,
  `docs/roadmap/gateway-decomposition.md`.
- Expected result: document becomes an archive with current boundary links.
- Verification: no current TODO suggests Gateway business/tool ownership.

### T3 — Update Message/Wake wording to Environment notifications

- Objective: remove outbox-as-current wording from current status docs.
- Scope: Gateway v2 and Message/Wake status docs.
- Expected result: wake source is Environment notification; outbox is not a current path.
- Verification: focused grep for current docs.

### T4 — Refresh backend optimization baseline

- Objective: replace old outbox-era optimization baseline with current service boundaries.
- Scope: `docs/roadmap/backend-architecture-optimization-recommendations.md`.
- Expected result: document names current main path and remaining discussion candidates.
- Verification: manual read plus grep for retired path wording.

### T5 — Sync oclow architecture notes

- Objective: update the long-lived oclow knowledge base so it does not preserve
  a conflicting tool/subscriber/Gateway story.
- Scope: `docs/novaic/README.md`,
  `docs/novaic/backend-architecture.md`,
  `docs/novaic/agent-perception-action-architecture.md`.
- Expected result: oclow names Environment notification, IM tools,
  payload interpretation tools, Blob/S3 payload storage, and Gateway thin-edge
  boundaries as current.
- Verification: oclow `rg` over stale terms and manual review of changed
  sections.

## Verification

- `rg` over current architecture/roadmap entry docs for misleading outbox/Gateway
  current-path wording.
- oclow `replace_section` and focused `rg` over `docs/novaic`.
- `git diff --check`.
- Manual read of the changed files.

## Closure Notes

Closed in this pass. No runtime behavior changed; deployment is not required for
doc-only cleanup.
