# write_step payload_ref mirroring success check

## Summary

Success. `R126` proves the payload data leaves step JSON, the final persisted `payload_ref` is mirrored into the stored observation, and both local and blob-backed paths are covered by focused tests.

## Evidence

- Payload removal and externalization path: `novaic-cortex/novaic_cortex/workspace.py:719-730`.
- Actual ref mirroring: `novaic-cortex/novaic_cortex/workspace.py:731-734`.
- Local payload stored-step assertions: `novaic-cortex/tests/test_step_index_outcome.py:117-146`, including observation-level `payload_ref`.
- Blob-backed payload observation mirror: `novaic-cortex/tests/test_step_index_outcome.py:148-191`.
- Payload inspection/readback suite passed with the step tests: `26 passed in 0.42s`.

## Criteria Map

- Source pointers for payload removal/storage: satisfied by `workspace.py:719-730`.
- Local payload readable and mirrored: satisfied by local test assertions and `read_payload`.
- Blob-backed payload replaces stale source ref: satisfied by blob test asserting top-level and observation `blob://cortex-payload/blob-1`.
- Focused tests verify readback: satisfied by `test_step_index_outcome.py` and `test_payload_inspection_api.py`.

## Execution Map

- Result `R126` inspected implementation and tests, found local stored-observation mirroring was implicit, added the direct assertion, and reran the relevant payload suites.

## Stress Test

- Local path: verifies the caller input remains unmutated while stored step observation receives the payload ref.
- External path: forces blob externalization with `BlobPayloadPolicy(threshold_bytes=4)` and verifies the stored observation uses the blob ref, not the original source ref.

## Residual Risk

- Non-blocking for `P146`: projection call sites and broader index completeness remain under sibling problems. Payload mirroring itself is now covered at the workspace boundary.

## Result IDs

- `R126`
