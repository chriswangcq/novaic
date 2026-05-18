# P565 Sandbox Service SDK Compatibility Residue Inventory Check

## Summary

Success. The inventory covers the sandbox service/core, SDK/client, runtime call boundary, wire base64, and mount/path surfaces. The evidence maps to the original concern: sandboxd remains the execution service boundary, LogicalFS supplies the mounted view, and no active compatibility branch or legacy executor bypass was found.

## Evidence

- P620 R612/C653 audited `novaic-sandbox-service`, classified sandboxd-internal execution/mount helpers as intended, and ran 13 focused service tests.
- P621 R618/C659 audited SDK/client/runtime boundaries via P623/P624/P625, classified SDK wire handling and runtime delegation, and ran SDK/Cortex/runtime focused suites.
- P622 R621/C662 audited wire base64 and mount/path residue via P628/P629, classified public-history vs private-wire surfaces, and ran Python/frontend/mount focused suites.
- P565 R622 aggregates the three closed children and names residual risks instead of hiding them.

## Criteria Map

- Records exact static scan commands and outputs: satisfied by child scan/evidence artifacts for service/core, SDK, runtime call sites, base64/history, and mount/path surfaces.
- Classifies compatibility/path/mount/base64 hits: satisfied by P620, P621, and P622 classification artifacts/checks.
- Confirms stdout/stderr base64 is only sandboxd wire encoding, not public LLM history: satisfied by P622/P628 plus passing projection/frontend redaction tests.
- Captures risky residue for P554 remediation: no high-confidence risky active residue was found; documented residuals are compatibility-reader and workspace hygiene, not remediation blockers.

## Execution Map

- T615 split into P620, P621, and P622.
- P621 further split SDK source, runtime call sites, and boundary coverage; P622 split public-history base64 and mount ownership.
- Each child reached success with checks before P565 rollup R622 was recorded.

## Stress Test

The check considered two failure modes that would make the inventory insufficient: a local/runtime execution path bypassing sandboxd, and raw screenshot/binary base64 leaking into public LLM/tool history. The child evidence explicitly tested both classes and classified residual parser compatibility as non-active-path.

## Residual Risk

- `step_result_projection.py` still parses legacy inline image/data URL shapes for compatibility, but current artifact/BlobRef projection is covered by tests.
- Generated untracked `__pycache__` files should be cleaned before final handoff.
- No remaining P565 code-boundary follow-up is required.

## Result IDs

- R622
- R612
- R618
- R621
