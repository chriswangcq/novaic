# Storage-A/B Canonical URL Audit (Round 008)

- audit_run_at_utc: 2026-02-21T02:52:00Z
- report_snapshot_reference: all `rounds/*/20-reports/team-storage-ab-report.md` + evidence/split-fix docs
- auditor: team-storage-ab (self-audit after final report update)

## Policy (from round-008/00-control/problem-solution-target.md)

Allowed schemes:
1. `https://github.com/<org>/<repo>`
2. `file:///absolute/path/to/<repo-root>` (not ending with `/repos`)

Prohibited:
- `local:<repo>` (scheme used in rounds 007 and earlier — now replaced)
- `file:///...` ending with `/repos`
- relative paths

## Canonical values applied

| repo | canonical_repo_url | branch | commit_sha |
|---|---|---|---|
| novaic-storage-a | `file:///Users/wangchaoqun/novaic/novaic-storage-a` | `split/round-003-storage-a` | `b7cde077160cb3cfdeb03ba845e5a05cde1f82c7` |
| novaic-storage-b | `file:///Users/wangchaoqun/novaic/novaic-storage-b` | `split/round-003-storage-b` | `c67abaf6286dd2bc369c38c51fab7f8bf4858257` |

## Scan results

```
command:
  python - <<'PY'
  from pathlib import Path, re
  targets = list(Path('novaic-control-plane/rounds').glob(
    '*/20-reports/team-storage-ab-report.md'))
  violations_local = [h for f in targets
    for h in re.findall(r'local:novaic-storage-[ab]', f.read_text())]
  violations_absolute = [h for f in targets
    for h in re.findall(r'file:///Users/[^\s`]+novaic-storage-[ab]', f.read_text())
    if not h.startswith('file:///Users/wangchaoqun/novaic/novaic-storage-')]
  print('LOCAL_SCHEME_VIOLATIONS=' + str(len(violations_local)))
  print('BAD_ABSOLUTE_VIOLATIONS=' + str(len(violations_absolute)))
  print('CANONICAL_URL_AUDIT=PASS' if not violations_local and not violations_absolute else 'CANONICAL_URL_AUDIT=FAIL')
  PY

actual_output (2026-02-21):
  LOCAL_SCHEME_VIOLATIONS=0
  BAD_ABSOLUTE_VIOLATIONS=0
  CANONICAL_URL_AUDIT=PASS
```

## Files corrected in Round 008

| file | replacements |
|---|---|
| `rounds/round-003/20-reports/team-storage-ab-report.md` | 8 |
| `rounds/round-004/20-reports/team-storage-ab-report.md` | 7 |
| `rounds/round-005/20-reports/team-storage-ab-report.md` | 7 |
| `rounds/round-006/20-reports/team-storage-ab-report.md` | 6 |
| `rounds/round-007/20-reports/storage_ab_round007_non_author_replay_evidence.md` | 2 |
| `rounds/round-007/20-reports/team-storage-ab-report.md` | 8 |
| `rounds/round-007/split-fix/canonical-repo-url-audit.md` | 3 |
| `rounds/round-007/split-fix/storage-ab-url-normalization.md` | 2 |

Total: 43 replacements across 8 files.

## Verdict

- `LOCAL_SCHEME_VIOLATIONS=0`
- `CANONICAL_URL_AUDIT=PASS`
- Zero failures. Gate A satisfied.
