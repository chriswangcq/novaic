# Check P177 / R162

Status: success

## Judgment

`R162` satisfies P177. It maps Cortex storage/projection refs, documents the stable `step_ref` versus final `payload_ref` contract, runs focused tests, and classifies request-side `payload_ref == step_ref` seeding as safe because Cortex normalization is final authority.

## Skeptical Review

- The result specifically checks the risky case: externalized payloads where final `payload_ref` differs from stable `step_ref`.
- Existing tests prove index entries and step files store the final blob payload ref while manifests preserve `source_payload_ref` and `step_ref`.
- The result correctly does not claim formatted-read behavior; that remains sibling P178.
- The initial mixed test command failure was a test package import collision and was resolved by separate passing Cortex/runtime runs.

## Residual Risk

No P177-specific residual risk. P178 remains open for formatted read/display projection behavior.
