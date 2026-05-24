# Add release-controller tests and CI guards

## Problem Definition

Release-controller core tests exist, but repository-level guards do not yet ensure they run alongside packaging and deploy-entry checks. The project needs CI-local checks that protect the release-controller from regressing before host deployment.

## Proposed Solution

Add or update local CI guard scripts so they verify:

- release-controller unit tests pass
- Dockerfile and Compose packaging files exist and contain required control-plane invariants
- Compose config renders with sample env when compose tooling is available
- deploy help exposes `release-controller-image`
- deploy rejects mutable controller image refs
- existing `services-image` and `factory-image` deploy paths remain discoverable

Prefer the existing `scripts/ci` guard style because root `pytest.ini` already points there.

## Acceptance Criteria

- A repository-level CI guard covers release-controller tests and packaging/deploy invariants.
- Guard is runnable through root pytest.
- Guard does not require Docker daemon access.
- Guard fails on mutable controller image refs.
- Release-controller unit tests still pass directly.

## Verification Plan

- Inspect existing `scripts/ci` tests.
- Add targeted guard.
- Run root `python3 -m pytest scripts/ci -q` or the specific guard if full suite is too broad.
- Run release-controller unit tests directly.

## Risks

- Nested pytest calls can be slow; keep the guard focused.
- Compose tooling may not be present in all environments, so static invariants should still provide coverage.

## Assumptions

- Full self-hosted release-controller automation is handled by later release-controller service work, not by GitHub Actions alone.
