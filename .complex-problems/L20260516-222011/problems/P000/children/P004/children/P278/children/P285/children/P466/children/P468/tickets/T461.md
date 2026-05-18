# Session hidden input inventory ticket

## Problem Definition

P468 must locate and classify hidden input surfaces in session/worker code before remediation. The target is direct environment reads, global mutable state, singleton config, duplicate branch switches, and test fixtures that may obscure production behavior.

## Proposed Solution

Run read-only guards over session coordinator code, task runtime handlers, subscriber/dispatcher setup, and tests. Save raw outputs, then inspect representative source slices around retained hits. Produce a hit classification with exact remediation targets for P469/P470.

## Acceptance Criteria

- Raw guard artifacts are saved under `.complex-problems/L20260516-222011/tmp/p468/`.
- The guard covers environment reads (`os.environ`, `getenv`), globals/singletons (`ServiceConfig`, module defaults), feature switches (`enable`, `disable`, `compat`, `legacy`, `fallback`), and duplicate branch patterns.
- Retained hits are classified as safe process-boundary configuration, test-only fixtures, or risky production hidden input.
- The result identifies exact files/functions needing remediation, or states source-backed no-op evidence.

## Verification Plan

Review guard output and representative source slices. Compare git status before/after to confirm this inventory child did not edit source.

## Risks

- Keyword guards can include many false positives such as fixture names and comments.
- Hidden inputs can be encoded as helper calls rather than raw `os.environ`.

## Assumptions

- This inventory child is read-only; fixes belong to later children.
