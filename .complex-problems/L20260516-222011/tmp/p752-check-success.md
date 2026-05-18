# Active docs and scripts semantic residue discovery check

## Summary

Status: success.

This was a one-go discovery ticket, so I applied a stricter check: it is only successful if it performed broad enough read-only scans, classified findings, and produced precise remediation candidates without pretending to fix them. `R736` meets that bar.

## Evidence

- `R736` lists the scanned surfaces and the exact active docs/scripts spot-read for boundary-sensitive content.
- `R736` distinguishes current acceptable docs (`docs/gateway/*`, `docs/runtime/tool-chain-dispatch.md`, Blob docs, `scripts/start.sh`) from remediation candidates.
- Remediation candidates are exact and actionable:
  - `docs/architecture/logicalfs-realtime-file-authority.md`
  - `docs/architecture/cortex.md`
  - `docs/cortex-architecture.md`
  - `docs/architecture/data-ownership.md`
- `R736` explicitly leaves service code and generated resource discovery to sibling problems `P753` and `P754`.

## Criteria Map

- Active docs/scripts scanned: satisfied by targeted `find` and `rg` scans plus spot reads.
- Findings classified: satisfied by current/acceptable classifications and exact remediation candidate list.
- Exact remediation candidates listed: satisfied.
- No product docs/scripts changed in this discovery ticket: satisfied in intent and execution; only ledger tmp files were created for this ticket, while product doc diffs already existed from earlier branches.

## Execution Map

- The ticket was bounded to docs/scripts discovery only.
- No implementation patch was performed.
- The result is sufficient input for the next remediation child.

## Stress Test

- Checked for over-broad false positives: roadmap/ticket legacy references were classified as historical work records rather than active docs.
- Checked for under-reporting: compared docs against actual `novaic-logicalfs/README.md` and `novaic-sandbox-service/main_sandbox_service.py`, which exposed the subtle LogicalFS/Cortex/Sandbox phrasing candidates.
- Checked that current shell/display contract docs already match the desired model.

## Residual Risk

This check does not claim the whole repository is semantically clean. It only closes active docs/scripts discovery. Service code and generated app/resource discovery remain open in sibling branches.
