# P000: Tool shell boundary construction plan

Status: done
Parent: none
Root: P000
Package: problems/P000
Body: problems/P000/README.md
Ticket(s): T000

## Problem
Create a detailed construction plan for implementing the previously designed unified tool shell boundary:

- Harness primitives outside shell: `shell`, `display`, `skill_begin`, `skill_end`, `sleep`.
- Environment interface capabilities inside shell: IM, subagent, device, blob/file, payload/Cortex reads, runtime inspection, business/environment APIs.
- Tool outputs as bounded text plus artifact/resource URI manifests.
- Cortex history stores manifests and refs, not raw sensory bytes.
- Display remains explicit perception.

This turn is plan/design only. Do not implement runtime code changes.

## Success Criteria
- Produce a detailed phased construction plan with dependency order, milestones, and rollback/cleanup gates.
- Break the work into concrete implementation tickets with file/module targets, acceptance criteria, verification commands, and deletion/compat cleanup expectations.
- Identify cross-repo boundaries between Runtime, Cortex, Device, Blob, Business, UI/Monitor, and tests.
- Include explicit dependency boundaries, hidden input risks, durable output/manifest contract, and context-bloat guardrails.
- Include a strategy for moving IM/subagent/device/payload capabilities into shell without breaking observability or safety.
- Include final cutover criteria proving old harness-level tools are removed or quarantined, not merely unused.

## Subproblems
- none

## Results
- R000

## Latest Check
C000

## Bodies
- Problem: problems/P000/README.md
- Ticket T000: problems/P000/tickets/T000.md
- Result R000: problems/P000/results/R000.md
- Check C000: problems/P000/checks/C000.md

## Follow-ups
- none
