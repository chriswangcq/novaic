# Backend Architecture Optimization Recommendations

| Field | Value |
|---|---|
| **Status** | Current discussion baseline, refreshed 2026-05-04 |
| **Created** | 2026-04-28 |
| **Scope** | Backend business and architecture logic after Environment, Cortex, Activity Timeline, and Blob Service cutovers. |
| **Primary Goal** | Keep the main path small, delete misleading old branches, and make future optimization discussions start from the current architecture. |

## Executive Summary

The current backend main path is:

```text
App
  -> Entangled action / sync
  -> Business Environment IM event + notification
  -> Business DispatchSubscriber
  -> Queue Service / Runtime workers
  -> Cortex scope tree + work trace
  -> LLM Factory + Runtime tool executors
  -> Business/Environment reply projection
  -> Activity Timeline projection through Entangled
```

This document is not a ticket list. It is a discussion baseline for choosing the
next optimization. If an item is worth doing, create a concrete PR ticket under
`docs/roadmap/tickets/`.

## Current Service Boundaries

| Service | Owns | Must Not Own |
|---|---|---|
| Gateway | Auth, App WS push/signaling, Entangled endpoint discovery, TURN, Blob edge | Agent wake, entity schema authority, tool registry, business orchestration |
| Entangled | Entity persistence, schema/action registration, sync WS | Agent-loop decisions, Cortex summaries, tool execution |
| Business | Product action hooks, Environment, SubAgent, Device orchestration, model/config product APIs | Queue execution state, Cortex context assembly, hidden memory inference |
| Queue / Runtime | Saga/task/session execution, LLM loop, Runtime tool executors | Product entity storage, Gateway edge, long-term memory |
| Cortex | LIFO scope tree, LLM context, reasoning/action/observation trace, payload refs, summary.md | User profile, automatic summary, chat-derived memory, business task system |
| Blob Service | Byte/blob storage and retrieval | Business meaning of files, scope semantics, tool interpretation |

## Current Continuity Rule

There is one continuity path:

```text
skill_end(report=...) -> current scope summary.md -> folded context in future wake
```

Do not reintroduce:

- wake summary / fallback summary
- chat-reply-derived memory
- profile inference from conversation text
- hidden Runtime payload summaries
- parallel history replay as continuity

## Optimization Candidates Worth Discussing

### 1. Documentation Drift / Misleading Residue

Historical roadmap and ticket files are useful archaeology, but active entry docs
must not describe old paths as current. The cleanup rule is:

- current docs state the current main path;
- historical docs say they are historical;
- old tickets can keep implementation history, but must not be linked as current SSOT.

Acceptance signal: a new maintainer can read `docs/README.md`,
`docs/architecture/overview.md`, `docs/architecture/service-topology.md`, and
`docs/runtime-architecture.md` without rebuilding an outbox/Gateway-centric
mental model.

### 2. Agent Monitor Product Semantics

Agent Monitor should show user-understandable activity, not developer payloads.
The desired projection is:

- observation
- reasoning
- action
- summary

Debug identifiers, raw MCP/HTTP bodies, result ids, and raw payloads belong in a
developer diagnostics surface, not the default monitor.

### 3. Blob / Large Payload UX

Blob Service is now the byte/object boundary. Potential future work:

- multipart upload for large App attachments;
- audio compression / streaming rather than large WAV blobs;
- clearer payload previews and explicit interpretation tools.

Do not put file bytes back into Cortex or Business metadata. They should keep
`blob://...` / payload refs plus product metadata.

### 4. Cortex Long-Term Growth

The agent-root scope tree can grow indefinitely. Any future compaction must stay
compatible with the current principle:

- no automatic hidden memory inference;
- no Runtime-created fake summaries;
- no raw payload default injection;
- compaction/fusion must be explicit, observable, and testable.

### 5. Environment IM History and Memory Boundary

Agent can explicitly observe bounded IM history through Environment tools. This
must remain different from automatic memory:

- IM history is an observation tool result.
- Long-term durable preference/profile updates require a separate explicit
  product decision.
- The system should never silently turn a chat reply into permanent memory.

## Already Closed / Do Not Reopen Without New Evidence

- Retired result-store service / tools-server / old MCP hot path.
- Gateway business entity proxy and Gateway tool registry.
- `message_outbox` / `chat_messages.lifecycle` as Agent-loop state.
- `subagent_report`, `subagent_query`, `subagent_cancel` LLM tools.
- `SPAWN_SUBAGENT` / `SUBAGENT_COMPLETED` wake message types.
- Runtime wake IM replay as continuity.
- Storage-A name/path; Blob Service is the current service boundary.

## How To Turn This Into Work

Use one mergeable ticket at a time:

1. analyze the current state;
2. create small tickets;
3. implement and test;
4. verify closure;
5. deploy / smoke when behavior changes;
6. commit and push.

Prefer physical deletion plus guardrails over fallback branches.
