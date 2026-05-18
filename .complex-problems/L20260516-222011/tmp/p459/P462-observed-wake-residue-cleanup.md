# Observed wake outbox residue cleanup

## Problem

Classify `OBSERVE_CREATE_WAKE_SAGA` source/test references and remove source residue if the active model no longer supports that effect type.

## Success Criteria

- Search source and tests for `OBSERVE_CREATE_WAKE_SAGA`.
- Remove production source residue if it is no longer needed.
- Keep or update tests only if they are negative guards for removed behavior.
- Run focused tests if source/test changes are made.
