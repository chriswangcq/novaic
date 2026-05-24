# Deploy execution-result persistence to API-host controller

## Problem

After local implementation is pushed, the API-host Release Controller must run the new code and prove historical run inspection exposes persisted execution results.

## Success Criteria

- API-host polling is paused before publishing the new controller persistence commit.
- New Release Controller image is built/pushed/deployed from the persistence commit.
- A remote verification run creates a persisted run record with `execution_result.results` visible from `/v1/runs/{run_id}` after the response.
- Polling is restored with `last_error=null`.
- Staging/prod pointers remain in the intended state unless explicitly changed.
