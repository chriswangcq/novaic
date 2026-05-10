# Sandbox execution extracted into independent service

## Summary

Completed the split implementation for extracting sandbox execution into an independent `sandboxd` server. Common now owns the service contract/client, `novaic-sandbox-service` owns process execution, Cortex server startup wires shell execution through sandboxd, deployment scripts start and monitor sandboxd, old Cortex command-wrapping residue is removed, and local verification passed.

## Done

- P001: Common sandboxd contract/client completed.
- P002: Independent sandboxd FastAPI service completed.
- P003: Cortex active server path wired to sandboxd runner port.
- P004: Service registry/start/deploy/log/status paths include sandboxd.
- P005: Stale Cortex command-wrapping residue removed.
- P006: Verification completed locally with tests, live service smoke, syntax checks, lint, and scans.

## Evidence

- Child checks C000-C005 are all success.
- Broad common tests: `148 passed`.
- Sandboxd tests: `5 passed`.
- Cortex wiring tests: `3 passed`; sandbox-focused suite `3 passed, 21 skipped` on local machine.
- Live sandboxd `/health` and `/v1/execute` smoke passed.

## Residual Risk

- Remote production deploy and Linux mount namespace smoke have not been executed in this run. The deploy path is prepared and should be run as the operational cutover proof.
