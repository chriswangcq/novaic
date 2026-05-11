# Deploy and verify result

## Summary

Deployed the repaired backend and verified production is no longer wedged. The repaired shell capability path succeeds and recent logs do not show the old failure signatures.

## Done

- `P007`: deployed all backend services with `./deploy services`; service status passed.
- `P008`: verified live session state and direct shell capability smoke.

## Verification

- Deployment fresh-smoke passed for all required backend logs.
- `./deploy status` showed all ports and runtime worker counts healthy.
- Production `tq_session_state` for the main agent is `no_active`.
- Direct `/v1/internal/shell` smoke with `agentctl im read --limit 1` returned `exit_code=0`.
- Recent post-deploy logs are clean for:
  - `missing or invalid X-Internal-Key`
  - `Tool message missing step_ref`
  - `no active root scope`
  - `FileNotFoundError`

## Known Gaps

- No full user-visible LLM reply smoke was forced; the specific repaired chain was before LLM provider generation and was verified directly.

## Artifacts

- `R005` backend deploy result.
- `R006` live recovery verification result.
