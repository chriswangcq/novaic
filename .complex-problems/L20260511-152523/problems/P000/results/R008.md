# Agent loop stall repair root result

## Summary

Diagnosed, repaired, deployed, and verified the production agent-loop stall after one round.

## Done

- `P001` diagnosed the deep failure chain:
  - shell `agentctl` lacked Cortex internal auth;
  - projected tool messages lacked top-level `step_ref`;
  - saga failure compensation dropped finalize/root/session context;
  - wake finalize failed and left the session stale active.
- `P002` fixed all three code defects with regression tests.
- `P003` deployed the repaired backend and verified production state.

## Verification

- Local focused tests:
  - runtime selected suite: `28 passed`;
  - Cortex selected suite: `37 passed`;
  - compensation/finalize/recovery suites included in runtime selected suite.
- Deployment:
  - `./deploy services` passed;
  - fresh-smoke passed;
  - `./deploy status` passed.
- Production:
  - affected session is `no_active`;
  - direct `agentctl im read --limit 1` shell smoke returned `exit_code=0`;
  - Cortex logged `/v1/meta/read status=200`;
  - recent logs are clean for old signatures.

## Known Gaps

- Historical failed saga rows remain as audit history, but they are pre-deploy and not active.
- I did not force a full LLM reply round; the repaired failure chain is before the provider call and was verified directly.

## Artifacts

- `R000` diagnosis result.
- `R004` code repair result.
- `R007` deploy and live verification result.
