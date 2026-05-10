# Design unified shell boundary and tool output contract

## Problem Definition

The current tool model has too many harness-level callable tools and too little semantic separation between environment IO, agent context control, visual perception, and resource storage. The user wants a more radical boundary:

- everything that is an environment interface should move inside shell-facing capabilities;
- only the smallest true harness primitives remain outside shell;
- tool outputs should default to bounded text plus resource/artifact URIs;
- display remains outside shell as explicit perception.

This ticket is design-only and must not change runtime code.

## Proposed Solution

Produce a detailed system design that defines:

- the shell-outside primitive set and the shell-inside capability set;
- the philosophy and invariants behind that boundary;
- a normalized `ToolOutput` / artifact manifest contract;
- the projections for current-turn LLM, historical Cortex context, monitor UI, and filesystem/blob resources;
- how IM/subagent/device/blob/payload operations become shell capabilities;
- safety, auditing, permission, and failure-mode handling;
- migration phases and residual risks.

## Acceptance Criteria

- The design explicitly lists what remains outside shell and what moves inside shell.
- The design gives a concrete output envelope with bounded text and artifact/resource URIs.
- The design explains how `display` differs from shell and why it remains outside.
- The design explains how `skill_begin`, `skill_end`, and `sleep` differ from shell capabilities.
- The design covers Cortex history, LLM context, monitor UI, filesystem/blob storage, and current-turn display.
- The design includes invariants, failure modes, migration phases, and non-goals.
- The design is recorded in the ledger as Markdown files and runtime code is untouched.

## Verification Plan

- Compare the design against the root success criteria.
- Check that it incorporates the prior file/display and tool optimization ledger conclusions.
- Verify no production code changes were made by this ticket.
- Validate and render the ledger.

## Risks

- The design may become too abstract unless it includes concrete schemas and operational flows.
- Moving IM/subagent operations into shell could blur safety boundaries unless capabilities are explicit, audited, and permissioned.
- Keeping `display` outside shell could be misunderstood as a second environment API unless its role as perception is tightly defined.

## Assumptions

- The user wants a design-level answer first, not implementation.
- `shell` can evolve from a narrow POSIX command runner into a broader environment operation substrate or CLI surface.
- `display` remains a model-visible perception primitive, not a generic API operation.
- `skill_begin` and `skill_end` are context-stack structure operations, and `sleep` is scheduler/yield semantics.
