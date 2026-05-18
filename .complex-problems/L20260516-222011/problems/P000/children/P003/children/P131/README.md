# Large-output and base64 leakage sweep

## Problem

Even if the main projection path is correct, stale fallback branches, tests, docs, and utility helpers can keep old inline-base64 or full-output behavior alive. A targeted sweep is needed to classify and remove active leakage residues.

## Success Criteria

- Source sweeps for `base64`, `data:image`, `screenshot`, `payload_ref`, `step_ref`, and `include_display` are performed and summarized.
- Remaining hits are classified as active-safe, provider-boundary-only, test fixture, documentation, or stale/dead.
- Any active unsafe hit is fixed or split into a more specific child problem.
- Stale documentation or tests that teach old behavior are updated or removed.
- A final sweep shows no unexplained active leakage paths remain.
