# Tool shell boundary system design

## Problem

Design a unified Agent Runtime tool boundary and tool output contract based on the latest direction:

- Keep only the minimum harness primitives outside shell: `shell`, `display`, `skill_begin`, `skill_end`, and `sleep`.
- Move environment interface tools into shell-facing capabilities: IM read/reply/history/search/context, subagent coordination, runtime/device/blob/payload/file APIs, and other environment operations.
- Treat the agent as the subject; the user, shell sandbox, device, blob/filesystem, queue/runtime, and subagents are environment resources that the agent can intentionally operate on.
- Keep `display` outside shell as the explicit perception surface for visual/file resources.
- Define tool outputs as bounded text plus artifact/resource URIs, with stable manifests suitable for Cortex history, monitor UI, and future shell APIs.

This turn is design-only. Do not implement code changes.

## Success Criteria

- Produce a detailed system design that explains the shell-inside/shell-outside boundary and why it is the right abstraction.
- Define a concrete tool output contract using default bounded text plus attachment/artifact/resource URIs.
- Define how Cortex history, current-turn LLM context, monitor UI, filesystem/blob storage, and `display` interact.
- Define how IM/subagent/device/blob/payload tools should become shell capabilities without losing safety, auditability, or explicit dependency boundaries.
- Identify invariants, failure modes, migration phases, and design risks.
- Record the design as ledger-backed files without changing runtime code.
