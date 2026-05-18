# Business/subscriber boundary discovery check

## Summary

Success. `R700` satisfies the discovery problem: it lists the Business/subscriber surfaces, separates ownership from neighboring services, identifies subscriber drain/aggregation responsibilities, and records hidden config / cleanup candidates for the already-planned remediation problem `P716`. The result intentionally does not fix stale wording; that is outside `P715` and belongs to `P716`.

## Evidence

- `R700` cites `novaic-business/main_business.py` as the Business service entrypoint and role boundary.
- `R700` cites `novaic-business/main_subscriber.py` and `novaic-business/business/subscribers/dispatch_subscriber.py` as the subscriber entrypoints and drain/aggregation implementation.
- `R700` records generated scan artifacts in `.complex-problems/L20260516-222011/tmp/p715/` for Business code, launch/docs references, and env/config references.
- `R700` identifies `docs/entangled-architecture.md` stale/ambiguous ownership wording as a concrete cleanup candidate for `P716`.

## Criteria Map

- Business and Subscriber entrypoints/launch references are listed: satisfied by `R700` Done and Artifacts sections, especially `business-file-tree.txt`, `business-scan.txt`, and `launch-doc-scan.txt`.
- Business domain/action-hook roles are separated from Queue, Runtime, Cortex, Gateway, Device, and Entangled ownership: satisfied by the boundary conclusions in `R700` Summary/Done.
- Subscriber drain/aggregation role is separated from wake/session ownership: satisfied by `R700` confirming subscriber only drains Environment notifications into Queue dispatch and does not own Cortex scope or wake/session lifecycle.
- Hidden env/config dependency candidates and cleanup candidates are listed: satisfied by `R700` confirming aggregation config is explicitly loaded once and listing docs/residue cleanup candidates for `P716`.

## Execution Map

- Discovery was read-only and generated scan artifacts.
- No code or docs were changed in this problem.
- Actual remediation is delegated to sibling problem `P716`, so this check only judges whether the discovery/map is complete enough to guide remediation.

## Stress Test

Plausible failure mode: the scan could miss stale docs that say Business owns Queue/session/runtime or that subscriber owns wake/session lifecycle. `R700` mitigates this by preserving broad `launch-doc-scan.txt` and explicitly instructing `P716` to classify active-vs-historical references instead of assuming the discovery is exhaustive cleanup.

## Residual Risk

Residual risk is non-blocking for `P715`: stale references may remain until `P716` runs, but `P715` has surfaced the concrete remediation targets and evidence artifacts needed to continue. No runtime behavior was changed by this discovery ticket.

## Result IDs

- R700
