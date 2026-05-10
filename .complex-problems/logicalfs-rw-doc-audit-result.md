# LogicalFS RO/RW documentation audit result

## Summary

Audited the LogicalFS / Blob / Cortex / Sandbox design docs against the narrowed
boundary. Fixed over-broad documentation language so the docs now describe
LogicalFS as only the Cortex/shell live `RO` / `RW` authority, while Blob remains
the cheap byte/file server for attachments, display bytes, artifact bytes, and
downloads.

## Done

- Reviewed `docs/architecture/logicalfs-realtime-file-authority.md`.
- Reviewed `docs/architecture/overview.md`.
- Reviewed `docs/architecture/service-topology.md`.
- Reviewed `docs/reference/blob-service.md`.
- Tightened the LogicalFS target diagram so only the Cortex / Runtime shell
  pipeline feeds LogicalFS; App/CLI/display/artifacts can use Blob directly when
  they do not need live RO/RW semantics.
- Renamed the overview link label from broad "实时文件权威边界" language to
  "LogicalFS RO/RW 实时边界".
- Removed the idea that LogicalFS exposes display/download handles.
- Added explicit wording that RO/RW files must be exported/copied to Blob before
  display/download.

## Verification

- Ran focused scans for over-broad or conflicting wording:
  - `all realtime`
  - `所有实时`
  - `除基础 Blob`
  - `所有文件服务`
  - `LogicalFS.*display`
  - `display.*LogicalFS`
  - `LogicalFS.*download`
  - `download.*LogicalFS`
  - `open_handle`
  - `BlobRef-backed`
  - `workspace/artifact`
  - `artifact file semantics`
  - `Business, App`
  - `Product / Agent semantics`
  - `实时文件权威边界`
  - `universal file`
- The remaining `display/download handles` matches are explicit negative
  statements saying LogicalFS does not provide those handles.
- Reviewed the focused git diff for the four audited docs.

## Known Gaps

- No code behavior was changed in this ticket; this is a design-document audit.
- The docs intentionally keep the current `CortexStore -> Blob object API` path
  labeled as transitional until implementation cutover happens.

## Artifacts

- `docs/architecture/logicalfs-realtime-file-authority.md`
- `docs/architecture/overview.md`
- `docs/architecture/service-topology.md`
- `docs/reference/blob-service.md`
