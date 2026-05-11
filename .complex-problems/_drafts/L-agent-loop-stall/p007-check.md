# Backend deploy check

## Summary

P007 is successful: production has the repaired code synced and all backend services/workers restarted and healthy.

## Evidence

- `./deploy services` exited with code `0`.
- Fresh-smoke checked all required logs after restart and all were fresh.
- `./deploy status` reported all service ports up and worker counts matching expectations.

## Criteria Map

- Deployment succeeds -> satisfied by `./deploy services` exit `0`.
- Fresh logs show restart activity -> satisfied by fresh-smoke output.
- Services/workers running -> satisfied by `./deploy status`.

## Execution Map

- `T007` / `R005` -> backend deployment and status verification.

## Stress Test

- If a required runtime worker failed to start, `start.sh` verification or `./deploy status` would show count mismatch.
- If a service log did not update after restart, fresh-smoke would fail.

## Residual Risk

- Deployment health does not itself prove the old stuck session recovered; that is covered by P008.

## Result IDs

- R005

## Blocking Gaps

- none
