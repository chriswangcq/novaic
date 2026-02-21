# Round 007 Canonical repo_url Audit

## Fix notes
- removed overly strict slash-count heuristic for `file:///` paths
- only rejects empty values and bare `/repos` collection directories

- reports_scanned: `7`
- failures: `3`

## Failures
- team-storage-ab: task1 repo_url not canonical 'file:///Users/wangchaoqun/novaic/novaic-storage-a'
- team-storage-ab: task2 repo_url not canonical 'file:///Users/wangchaoqun/novaic/novaic-storage-a'
- team-storage-ab: task3 repo_url not canonical 'file:///Users/wangchaoqun/novaic/novaic-storage-a'

## Marker
- `ROUND007_CANONICAL_REPO_URL_AUDIT_COMPLETED`
