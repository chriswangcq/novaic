# Round 004 Feedback

## Round decision
- decision: CONDITIONAL_PASS
- owner: Program Owner

## Feedback summary
- P0: none
- P1:
  - Desktop team report is still template-only and has no executable evidence block. Round cannot close as PASS until `20-reports/team-desktop-report.md` is fully populated with commit SHA, migrated paths, and split startup replay markers.
  - Tools team raised a real runtime wiring gap: Tauri startup path can still launch tools from monorepo path in some flows. This is split adoption risk and must be closed in next round with code change evidence.
- P2:
  - Several teams still reference local file remotes as `repo_url`; acceptable for split execution rehearsal, but next round must use canonical official repo URLs in reports.
  - Evidence quality is uneven (some reports include minimal markers only). Next round should require explicit before/after path mapping per migrated module.

## Compliance check
- DONE without commit_sha: no
- DONE without migrated_paths mapping: no
- script-only updates without code move: no
- missing owner/target_round in Decision Needed: no

## Gate check
- Gate A: PASS (submitted DONE items include commit SHA and migrated path mapping)
- Gate B: CONDITIONAL_PASS (split repo startup/health evidence exists for multiple services, but Desktop report evidence is missing)
- Gate C: CONDITIONAL_PASS (cross-repo paths are proven for API and Storage; Desktop split-runtime path not yet formally reported)
- Gate D: CONDITIONAL_PASS (execution discipline improved, but one team did not submit required executable report format)

## Mandatory focus for next round
- Desktop must complete round report with hard evidence; no carry-over template placeholders are allowed.
- Close Tauri tools-server split wiring gap with code diff in desktop startup path and replay marker from split mode.
- Enforce canonical repo URL field policy in all team reports (no directory-level or ambiguous local path URLs).
- Require one end-to-end split chain per team that can be replayed by non-authors.
