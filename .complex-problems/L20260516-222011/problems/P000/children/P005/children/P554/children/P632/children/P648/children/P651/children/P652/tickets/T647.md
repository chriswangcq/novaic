# Require Explicit Cortex API URL in Test Helper

## Problem Definition

The shared Cortex test helper still provides a default `cortex_api_url="http://cortex.test"`. That hides a constructor dependency and weakens tests that should explicitly prove how the Cortex API URL reaches `Cortex`, `Sandbox`, and LogicalFS.

## Proposed Solution

Remove the default URL from `make_cortex_with_store` and update every call site to pass `cortex_api_url="http://cortex.test"` explicitly. Keep production code unchanged except if a test isolation helper is needed.

## Acceptance Criteria

- `make_cortex_with_store` has no default value for `cortex_api_url`.
- All existing call sites pass an explicit fake URL.
- `rg "cortex_api_url: str =" novaic-cortex/novaic_cortex novaic-cortex/cortex_tests novaic-cortex/tests` returns no hidden helper/default constructor match.
- Focused runtime/helper tests pass.

## Verification Plan

Run a targeted replacement audit with `rg`, then run the Cortex tests that use `make_cortex_with_store`, or at minimum a representative subset plus the fallback scan.

## Risks

- Many tests use the helper, so a mechanical update can miss a call site.
- A broad focused test set may be needed to catch signature mismatches.

## Assumptions

- `http://cortex.test` remains acceptable as an explicit fake URL in tests.
