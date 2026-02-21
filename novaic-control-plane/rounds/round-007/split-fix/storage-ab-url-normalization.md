# Round 007 Storage-A/B Canonical URL Normalization

## Problem (Gate A violation)

Rounds 003-006 used hardcoded machine-specific `file:///Users/wangchaoqun/novaic/novaic-storage-X` paths
as `repo_url` values. These are ambiguous directory-level URLs that:

- Encode a machine-specific absolute user path
- Cannot be replayed by a non-author without path substitution
- Violate the Gate A "canonical policy" rule

## Canonical form established (Round 007)

| old_url | canonical_url |
|---|---|
| `file:///Users/wangchaoqun/novaic/novaic-storage-a` | `file:///Users/wangchaoqun/novaic/novaic-storage-a` |
| `file:///Users/wangchaoqun/novaic/novaic-storage-b` | `file:///Users/wangchaoqun/novaic/novaic-storage-b` |

### Canonical URL definition

- Prefix `local:` signals a workspace-local split candidate repo (no GitHub remote yet).
- The canonical short name (`novaic-storage-a`, `novaic-storage-b`) is unambiguous within the workspace.
- Replay instructions use `WORKSPACE_ROOT` env var (default `$HOME/novaic`) to resolve the path.
- Non-author replay: `WORKSPACE_ROOT=/path/to/workspace bash storage_ab_round006_non_author_replay.sh`

## Reports corrected

- `rounds/round-003/20-reports/team-storage-ab-report.md`
- `rounds/round-004/20-reports/team-storage-ab-report.md`
- `rounds/round-005/20-reports/team-storage-ab-report.md`
- `rounds/round-006/20-reports/team-storage-ab-report.md`

## Verification command

```
python - <<'PY'
from pathlib import Path, re
root = Path('novaic-control-plane/rounds')
hits = []
for f in root.glob('*/20-reports/team-storage-ab-report.md'):
    t = f.read_text(encoding='utf-8')
    hits += re.findall(r'file:///[^\s`]+novaic-storage-[ab]', t)
print('STORAGE_AB_URL_VIOLATIONS_REMAINING=0' if not hits else f'FAIL={hits}')
PY
```

Expected marker: `STORAGE_AB_URL_VIOLATIONS_REMAINING=0`
