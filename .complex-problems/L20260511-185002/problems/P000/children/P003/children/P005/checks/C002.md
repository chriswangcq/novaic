# agentctl Blob contract audit check

## Summary

P005 is solved by R002. The active `agentctl` CLI paths were inspected and verified with targeted tests; no raw binary or base64 artifact stdout path was found.

## Evidence

- `_get_blob` rejects non-Blob URLs and reads audio bytes from Blob Service.
- `_agentctl_media` base64-encodes audio only for the Factory request body and prints a text answer plus metadata, not audio bytes.
- `_agentctl_im` and `_agentctl_subagent` only post/read JSON metadata and do not download attachment bytes.
- Runtime and Cortex tests covering user content, shell output contract, tool output contract, internal auth, schemas, and Blob payload client passed.

## Criteria Map

- `agentctl media audio-qa` consumes Blob input and does not print raw audio bytes: satisfied by code inspection and user content tests.
- IM commands do not inline attachment bytes: satisfied by code inspection of IM paths and tests rendering attachment handling through Blob references.
- Subagent spawn output is metadata only: satisfied by code inspection.
- Violations fixed or recorded: no active violations found.

## Execution Map

- R002 performed code audit and ran targeted tests.
- Verification commands produced `16 passed` in `novaic-agent-runtime` and `16 passed` in `novaic-cortex`.

## Stress Test

- The main plausible artifact risk, audio data, was traced end to end: Blob URI input -> Blob Service GET -> Factory request -> text-only CLI stdout.
- The IM attachment path was checked for download behavior; no file-byte retrieval exists in `agentctl im`.

## Residual Risk

- IM APIs can return user text that happens to look like base64. That is content text, not binary artifact transport, and is outside the Blob contract violation class.

## Result IDs

- R002
