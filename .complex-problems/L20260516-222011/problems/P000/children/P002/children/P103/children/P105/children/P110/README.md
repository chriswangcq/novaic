# Agentctl Media Audio-QA CLI Contract Audit

## Problem

Audio/media helper actions migrated behind shell should be reachable through `agentctl media audio-qa` and should not rely on stale direct tool exposure for normal agent behavior.

## Success Criteria

- Locate `agentctl media audio-qa` implementation and registration.
- Verify shell tool schema/docs mention the command.
- Verify output remains text/artifact-contract compatible and does not introduce hidden binary/base64 LLM payloads.
- Run focused tests or safe help checks; fix bounded gaps found.
