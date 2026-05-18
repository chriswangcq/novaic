# Finish Business residue classification, cleanup, and tests

## Problem
T067 removed many historical Business comments, but active implementation scans still show ambiguous residue in `novaic-business/business`: a no-op `ensure_agent_stub` helper and call site, `get_entity_def` minimal stub wording/path, retired health stub wording, and environment IM endpoint names that must be explicitly classified as current shell boundary or removed. Focused Business tests were not yet run after the cleanup.

## Success Criteria
- Every remaining active scan hit in `novaic-business/business` and `novaic-business/main_subscriber.py` is either removed as residue or documented as current architecture with non-misleading wording.
- No no-op compatibility helper remains on the active path unless it has a current, tested purpose.
- Tests are updated if removed helpers were monkeypatched or assumed.
- Focused Business tests pass for dispatch subscriber, subagent spawn/state, environment internal API, assembler factory, schema/entity boundaries.
- A final active residue scan is run and remaining hits are listed with explicit classification.

## Suggested Checks
- `rg -n "PR-|Pre-|Post-|Wave|fallback|compat|migration|migrate|TODO|FIXME|im_read|im_reply|payload_read|audio_qa|subagent_spawn|chat_reply|direct tool|direct-tool|connesive|stub" novaic-business/business novaic-business/main_subscriber.py -g '*.py'`
- Focused `pytest` commands under `novaic-business` after inspecting available tests.
