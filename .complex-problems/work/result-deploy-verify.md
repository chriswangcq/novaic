# Deploy verification result

## Summary

Deployed the runtime/common fixes and verified production stayed healthy. A first deploy revealed uvicorn access logs were still emitted by the actual `main_novaic.py queue-service` entrypoint; that gap was fixed with `access_log=False`, tested, redeployed, and verified by log count differential.

## Done

- Ran combined targeted tests before deployment.
- Deployed with `./deploy runtime` twice: once for the FSM/common fixes, then again after closing the uvicorn entrypoint gap.
- Added and tested a guard that `main_novaic.py` service entrypoints disable uvicorn access logs.
- Verified production disk, Redis, queue session state, and notification status after deployment.
- Verified worker `httpx` claim spam and queue-service uvicorn claim spam no longer increase after deployment.

## Verification

- Runtime tests: `12 passed in 0.09s`.
- Common tests: `21 passed in 0.25s`.
- Deploy: `novaic-agent-runtime 已部署（全部服务已重启）`.
- Disk: `/dev/nvme0n1p2` at `16G used / 79G free / 17%`.
- Redis: `PONG`, `rdb_last_bgsave_status:ok`, `rdb_bgsave_in_progress:0`.
- Session state: affected agent/subagent is `no_active`.
- Log differential over 15 seconds after second deploy:
  - `task-worker-control-1.log` line count unchanged, claim `httpx` count unchanged.
  - `task-worker-execution-1.log` line count unchanged, claim `httpx` count unchanged.
  - `queue-service.log` line count unchanged, uvicorn claim count unchanged.

## Known Gaps

- Old historical log files still contain previous noisy lines, but post-deploy counts stopped growing.

## Artifacts

- `novaic-agent-runtime/main_novaic.py`
- `novaic-agent-runtime/tests/test_pr346_uvicorn_access_log_disabled.py`
- Production verification command output in this session.
