# PR-170D — Payload Interpretation End-to-End Guards

| Field | Value |
| --- | --- |
| Status | `[open]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Repos | `novaic-common`, `novaic-cortex`, `novaic-agent-runtime`, docs |
| Parent | PR-170 |

## Goal

Close PR-170 with cross-repo guards and smoke tests proving interpretation is explicit, bounded, and not a hidden summary path.

## Current-State Analysis

Read/search have existing integration tests. Summarize/QA need comparable cross-repo guardrails after schema, Cortex, and Runtime are wired.

## Implementation Checklist

- [ ] Add tool-schema/executor/monitor contract guard covering all four payload tools.
- [ ] Add smoke tests for explicit summarize/QA result shapes.
- [ ] Confirm trace projection maps interpretation as observation.
- [ ] Update architecture docs from future-tool wording to active-tool wording.
- [ ] Run relevant full test suites.
- [ ] Deploy services.
- [ ] Commit and push parent docs/submodule pointers.

## Done Criteria

- `payload_summarize` / `payload_qa` are active only through explicit tool calls.
- Docs, contracts, tests, and deployment all agree.
