# Follow-up: Reconcile current perception/action architecture doc with shell-first subagent/audio contract

## Problem
`docs/roadmap/agent-perception-action-architecture.md` still describes `audio_qa`, `subagent_spawn`, `im_read`, and payload tools using the older direct-tool mental model. This conflicts with the current shell-first contract where IM/subagent/audio/payload operations are CLI capabilities mediated through `shell`, with `display`, `sleep`, and skill lifecycle remaining direct harness tools.

## Success Criteria
- Update `docs/roadmap/agent-perception-action-architecture.md` so current architecture text reflects the shell-first capability boundary.
- Preserve historical context if useful, but clearly mark obsolete direct-tool lists as historical or remove them.
- Focused search in that doc should no longer present `audio_qa` or `subagent_spawn` as active direct tools.
- Do not rewrite historical PR ticket files unless this ticket finds they are linked as current guidance.
