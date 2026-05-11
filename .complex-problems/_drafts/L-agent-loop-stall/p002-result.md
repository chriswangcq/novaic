# Chained stall code repair result

## Summary

Completed the code repairs for the identified three-link stall chain: shell capability internal auth, top-level tool `step_ref` projection, and wake-finalize compensation context preservation.

## Done

- `P004` repaired shell capability internal auth:
  - runtime passes `NOVAIC_CORTEX_INTERNAL_KEY`;
  - shell capability allowlist accepts it;
  - generated `agentctl` attaches `X-Internal-Key` to Cortex internal calls only.
- `P005` repaired context event projection:
  - projected tool messages now include top-level `step_ref`;
  - diagnostic `_metadata.payload_ref` remains intact.
- `P006` repaired compensation finalize context:
  - failed wake/think/actions sagas now create wake-finalize compensation with preserved root/path/session/stack metadata.

## Verification

- `novaic-agent-runtime` shell capability tests: `6 passed`.
- `novaic-cortex` shell internal auth tests: `2 passed`.
- `novaic-cortex` context projection/read/write tests: `35 passed`.
- `novaic-agent-runtime` compensation/finalize/recovery tests: `22 passed`.

## Known Gaps

- Need a final integrated test/deploy/recovery verification phase to prove the live stuck session is cleared and new agent-loop messages progress normally.

## Artifacts

- `R001` shell internal auth result.
- `R002` step-ref projection result.
- `R003` compensation context result.
