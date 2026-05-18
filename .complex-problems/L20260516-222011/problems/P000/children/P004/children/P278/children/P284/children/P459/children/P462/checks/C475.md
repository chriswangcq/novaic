# Check: P462 observed wake outbox residue cleanup

## Result IDs

- R449

## Status

not_success

## Evidence

- R449 found a production source residue: `novaic-agent-runtime/queue_service/session_outbox.py:30`.
- R449 did not remove the residue.
- Tests still import/reference the production constant as a negative-guard marker.

## Criteria Map

- Search source/tests: satisfied.
- Remove production source residue if unused: not satisfied.
- Preserve/update tests as negative guards: not satisfied yet.
- Run focused tests after changes: not satisfied yet.

## Execution Map

- Reviewed R449.
- Determined the ticket cannot be marked success because it found but did not remove the production residue.
- No implementation work performed during this check.

## Stress Test

The tempting shortcut would be to classify the constant as harmless because it is not in `SUPPORTED_EFFECT_TYPES`. That is not clean enough under the user's “旧代码清理干净” rule: the production class should not expose an obsolete unsupported effect constant.

## Residual Risk

Old observed-wake effect naming can mislead future code into using a removed model.
