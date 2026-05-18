# workspace tool step normalization and index success check

## Summary

Success. `R132` solves `P142` with child evidence covering validation, payload externalization/mirroring, compact index metadata, corrupt-index behavior, and active call-site wiring.

## Evidence

- `R125`: `normalize_step` rejects inline `result` and invalid/missing observation.
- `R126`: payload data is externalized and actual `payload_ref` is mirrored into stored observation.
- `R127`: index rows preserve metadata and corrupt rows fail loudly; metadata edge gaps were fixed.
- `R131`: active Cortex API/runtime/bypass paths use the reviewed projection boundary.

## Criteria Map

- `normalize_step`, `write_step`, `write_step_projection` source pointers: satisfied across child results.
- Inline `result` rejection and observation requirement: satisfied by `R125` and `R128`.
- Raw payload externalization and actual `payload_ref` mirroring: satisfied by `R126`.
- Index entries include `step_ref`, `payload_ref`, duration/tool/status, and artifact marker: satisfied by `R127`.
- Active wiring: satisfied by `R131`.

## Execution Map

- Parent split into P145-P148.
- P148 further split into P149-P151 to avoid hand-waving call-site coverage.
- All children closed with success checks before this parent result.

## Stress Test

- The work includes behavioral tests for malformed input, missing observation, local/blob payloads, zero duration, observation artifacts, corrupt index JSONL, API inline result rejection, runtime producer shape, and static bypass residue.

## Residual Risk

- No blocking residual risk for `P142`. Broader context JSONL and API materialization siblings remain under `P143`/`P144`.

## Result IDs

- `R132`
- Child evidence: `R125`, `R126`, `R127`, `R131`
