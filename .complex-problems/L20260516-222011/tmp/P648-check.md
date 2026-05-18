# P648 strict success check

## Status

success

## Result IDs

- R643

## Evidence

- Broad final scan `.complex-problems/L20260516-222011/tmp/P648-final-broad-scan.txt` found no active Cortex local shell execution fallback and no remaining `localhost:19996` default in runtime code.
- Cortex `Sandbox` returns a fail-closed error when no sandbox executor is configured: `Sandbox executor is not configured... must go through sandboxd`.
- Shell execution subprocess work is isolated to `novaic-sandbox-service/sandbox_service/core/process.py`, which is the intended sandboxd service process runner, not a Cortex fallback path.
- P651/P652 closed the implicit Cortex API URL fallback discovered during P648.
- Focused tests passed: `20 passed` for shell/sandbox/API paths and `86 passed` for helper users.

## Criteria Map

- Scan runtime/cortex/sandbox code for local shell fallback/direct subprocess/local execution/fallback terms: satisfied by P648 final broad scan.
- Classify remaining hits: satisfied; sandbox service subprocess is intended worker implementation, agent-runtime Popen is supervisor process launch, tests are guardrails, and Cortex sandbox code fails closed.
- Remove or create follow-up for active hidden fallback: satisfied; the only active residue found was implicit Cortex API URL and it was removed through P651/P652.

## Execution Map

- Initial audit found no local process fallback but detected implicit service URL fallback.
- Spawned P651, which removed production implicit URL defaults.
- Spawned P652 follow-up, which removed the remaining test-helper default.
- Reran scans and targeted tests.

## Stress Test

The check did not stop at the first green test: it re-ran broad string scans after fixes and treated a test-helper default as a real follow-up gap. Remaining hits are classified by service boundary rather than ignored.

## Residual Risk

Low for local shell fallback. A separate broader architecture concern remains in `common/http/clients.py` wording about bootstrap fallback, but it is outside this shell fallback ticket and should be handled by a separate explicit-dependency audit if needed.
