# P004 success check

## Status

success

## Results Reviewed

- R003

## Evidence

- `scripts/start.sh` and `deploy` pass shell syntax checks.
- `ServiceConfig` resolves sandboxd URL and port from strict config.
- Deploy fresh-smoke lint now requires `sandboxd.log`.
- Source scans show sandboxd in start/deploy active wiring.

## Criteria Map

- Stable URL/port in config: satisfied by `services.json` and `ServiceConfig`.
- Start/stop/wait/log in local backend script: satisfied by `scripts/start.sh`.
- Cortex receives `--sandboxd-url`: satisfied by `scripts/start.sh`.
- Deploy/status/log commands include sandboxd: satisfied by `deploy`.
- No fallback added: no fallback code was introduced; Cortex `main_cortex` still requires `--sandboxd-url`.

## Execution Map

- Updated config and shell/deploy scripts.
- Ran syntax and config smoke checks.

## Stress Test

- Lint guards fresh log smoke to prevent future deploy drift.
- `bash -n` catches shell syntax regressions before deployment.

## Residual Risk

- Remote deployment execution remains for P006.
