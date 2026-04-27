# PR-76 — Add Cortex boundary guardrails

| Field | Value |
|---|---|
| **Ticket** | PR-76 |
| **Status** | `[ ]` |
| **Opened** | 2026-04-27 |
| **Owner** | __ |
| **Severity** | P1 regression risk — removed memory/summary concepts can silently return without a focused boundary check. |
| **Blocks** | Future Cortex cleanup work. |
| **Blocked by** | PR-74, PR-75 |
| **Invariant** | Cortex source must not grow non-Cortex responsibilities: auto summary, user profile, business tasks, memory inference, wake summary, chat-reply memory, or parallel summary channels. |

## Intent

Make the new Cortex boundary executable.

After PR-74 and PR-75, add a small CI/test guard that fails when active Cortex code reintroduces concepts that do not belong to Cortex.

## Required Behavior

- Add a lint or pytest-based boundary test over active Cortex source.
- Ban active-code references to retired concepts unless explicitly allowlisted in docs/tombstone tests.
- Banned concepts include:
  - automatic summary generation
  - user profile ownership
  - business task system ownership
  - memory inference or memory recall proxying
  - `wake summary`
  - deriving long-term memory from `chat_reply`
  - multiple parallel summary producers
- Document the allowlist policy so future contributors know how to add a legitimate exception.

## Acceptance Criteria

- CI fails if active Cortex code introduces a banned boundary concept.
- Boundary test output tells the developer which file and pattern violated the rule.
- Docs clarify Cortex's only two jobs: maintain the LIFO scope tree and assemble LLM context from that tree.
- The test is not brittle against ticket files, tombstones, or historical docs.

## Engineering Checklist

### Unit Tests

- `[ ]` Add boundary test or script with fixtures proving it catches at least two banned patterns.
- `[ ]` Add allowlist fixture proving historical docs/tombstones can mention banned terms without failing.
- `[ ]` Run full Cortex tests.
- `[ ]` Run parent-level CI/lint if the guard is wired outside the Cortex submodule.

### Smoke Tests

- `[ ]` Run the boundary guard locally against the real repository and capture clean output.
- `[ ]` Temporarily inject a banned phrase in a scratch file or fixture and prove the guard fails, then remove it before commit.
- `[ ]` Inspect a fresh LLM request and confirm no retired prompt markers or summary routes are present.

### Deployment

- `[ ]` Deploy if production code changed; otherwise record that this PR is CI/docs-only and no service deploy is required.
- `[ ]` If deployed, run `./deploy status`; if not deployed, still run the relevant health or test evidence needed by the PR template.
- `[ ]` Capture CI evidence after push.

### GitHub / Commit

- `[ ]` Commit guard, docs, tests, and this ticket update as one PR-sized commit.
- `[ ]` Commit message should reference `PR-76`.
- `[ ]` Push the branch and include boundary guard output plus CI status in the PR description.

## Out of Scope

- Further product behavior changes.
- Moving business features to another service.
- Modifying LLM tool descriptions; PR-77 owns that.
