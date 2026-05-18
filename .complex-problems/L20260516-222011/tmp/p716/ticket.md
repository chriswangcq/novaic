# Business/subscriber residue remediation ticket

## Problem Definition

Business/subscriber boundary discovery identified potentially stale or ambiguous active claims and hidden-dependency risk around Business, Subscriber, Queue, Runtime, Cortex, Gateway, Device, and Entangled ownership. These findings need to be reviewed against current code and patched where safe, without collapsing Business/subscriber responsibilities into neighboring service ownership.

## Proposed Solution

Perform a focused cleanup pass using the P715 artifacts as input. Classify each candidate as active stale claim, intentional historical/current comparison, test-only fixture, or broad/risky follow-up. Patch safe active stale claims in docs or code comments, especially the `docs/entangled-architecture.md` wording about entity CRUD writes through Gateway auth and any text implying subscriber owns wake/session lifecycle or Business owns Queue/Runtime state. Re-run focused residue scans and relevant lint/test commands after changes.

## Acceptance Criteria

- Every cleanup candidate from P715 is dispositioned as patched, intentionally retained, test-only, or follow-up-worthy.
- Safe active stale Business/subscriber ownership claims are patched.
- No new broad compatibility/fallback path is introduced.
- Any risky or too-large cleanup is split into a follow-up problem instead of hidden in prose.
- Verification includes focused scans and at least one relevant docs/service-boundary lint or test command.

## Verification Plan

Run focused `rg` scans over `novaic-business`, `docs`, `scripts`, and launch surfaces for Business/subscriber plus Queue/Runtime/Cortex/Gateway/Device/Entangled terms. Run existing architecture/status lints that cover docs and boundary language where available. If code changes are needed, run the narrowest relevant Python tests or import/compile checks.

## Risks

- Some stale-looking docs may be intentional historical comparison text and should not be deleted blindly.
- Entangled/Gateway/Business ownership wording may reflect a still-active route in app or API code; patch only after checking current route ownership.
- Broad docs cleanup could sprawl; split follow-ups if the remediation becomes larger than the Business/subscriber boundary.

## Assumptions

- P715 discovery artifacts are trusted as the starting map.
- Cleanup should favor current active architecture over backwards compatibility wording.
- Historical comparison text can remain only if it is clearly labeled as not current behavior.
