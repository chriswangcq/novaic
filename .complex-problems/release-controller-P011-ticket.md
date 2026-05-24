# Verify release-controller core unit tests

## Problem Definition

The release-controller core needs explicit unit test coverage for the safety and behavior rules that make it suitable as a central release control plane.

## Proposed Solution

Review and run the tests added across the P002 child slices. Add any missing focused tests needed to cover:

- branch mapping for `main`, `preview/*`, and `release/*`
- immutable image ref validation
- state persistence across reload
- current/previous pointer rollover
- dry-run command planning
- API behavior when FastAPI TestClient is available

## Acceptance Criteria

- Core test suite runs locally.
- Tests cover the required branch mapping cases.
- Tests cover accepted and rejected immutable image refs.
- Tests cover state persistence across store reload.
- Tests cover current/previous pointer updates.
- Tests cover dry-run command planning and dry-run runner behavior.
- Tests cover key API endpoints in-process.

## Verification Plan

- Run `PYTHONPATH=novaic-release-controller python3 -m pytest novaic-release-controller/tests -q`.
- Inspect test names and assertions against each acceptance criterion.
- Record any missing coverage as a follow-up if needed.

## Risks

- Passing tests that only exercise happy paths would leave release safety rules under-proven.
- API tests may depend on FastAPI/TestClient availability in the local environment.

## Assumptions

- CI guard wiring belongs to P004; this ticket only proves the core unit suite exists and passes locally.
