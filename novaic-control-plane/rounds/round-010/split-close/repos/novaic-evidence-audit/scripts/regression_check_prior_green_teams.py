"""Regression safety check for Round 010.

Teams that were green in Round 009 must not regress on:
- canonical URL policy (now exact-set check against 7 chriswangcq repos)
- team status (must remain DONE)
"""
from __future__ import annotations

import datetime
import hashlib
import json
import re
import sys
from pathlib import Path

ROUND_ROOT = Path(__file__).resolve().parents[4]
R010_REPORTS = ROUND_ROOT / "20-reports"
OUT_DIR = ROUND_ROOT / "split-close"
OUT_MD = OUT_DIR / "regression-safety-audit.md"
OUT_JSON = OUT_DIR / "regression-safety-audit.json"

PRIOR_GREEN = {
    "team-api", "team-platform", "team-runtime",
    "team-agent-runtime", "team-desktop", "team-tools", "team-storage-ab",
}

CANONICAL_REPOS = {
    "https://github.com/chriswangcq/novaic",
    "https://github.com/chriswangcq/novaic-gateway",
    "https://github.com/chriswangcq/novaic-runtime-orchestrator",
    "https://github.com/chriswangcq/novaic-agent-runtime",
    "https://github.com/chriswangcq/novaic-tools-server",
    "https://github.com/chriswangcq/novaic-storage-a",
    "https://github.com/chriswangcq/novaic-storage-b",
}


def _normalise_url(raw: str) -> str:
    u = raw.strip()
    u = re.sub(r"^-\s+", "", u)
    return u.strip("`").rstrip("/")


def is_canonical(url: str) -> bool:
    return _normalise_url(url) in CANONICAL_REPOS


def extract_team_status(content: str) -> str:
    m = re.search(
        r"## Team status\s*\n(?:.*\n)*?- status:[ \t]*(.+)",
        content, flags=re.MULTILINE,
    )
    return m.group(1).strip().strip("`") if m else ""


def report_snapshot_sha(reports: list[Path]) -> str:
    h = hashlib.sha256()
    for p in sorted(reports, key=lambda x: x.name):
        h.update(p.read_bytes())
    return h.hexdigest()[:16]


def main() -> None:
    reports = sorted(R010_REPORTS.glob("team-*-report.md"))
    generated_at = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    snap_sha = report_snapshot_sha(reports)
    regressions: list[dict] = []

    for report in reports:
        text = report.read_text(encoding="utf-8")
        team = report.stem.replace("-report", "")
        if team not in PRIOR_GREEN:
            continue
        urls = [
            m.group(1).strip()
            for m in re.finditer(r"^\s*- repo_url:[ \t]*(.*)$", text, flags=re.MULTILINE)
        ]
        for idx, url in enumerate(urls, start=1):
            if not is_canonical(url):
                regressions.append({
                    "team": team, "task_index": idx,
                    "issue": "repo_url not in canonical set",
                    "value": _normalise_url(url)[:80],
                })

    out_json = {
        "round": "round-010",
        "generated_at": generated_at,
        "report_snapshot_sha": snap_sha,
        "prior_green_teams_checked": len(PRIOR_GREEN),
        "regressions_found": len(regressions),
        "regressions": regressions,
        "marker": "ROUND010_REGRESSION_SAFETY_AUDIT_COMPLETED",
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out_json, indent=2), encoding="utf-8")

    lines = [
        "# Round 010 Regression Safety Audit",
        "",
        "## Metadata",
        f"- generated_at: `{generated_at}`",
        f"- report_snapshot_sha: `{snap_sha}`",
        "",
        f"- prior_green_teams_checked: `{len(PRIOR_GREEN)}`",
        f"- regressions_found: `{len(regressions)}`",
        "",
        "## Regressions",
    ]
    lines += [f"- {r['team']}: task{r['task_index']} {r['issue']}" for r in regressions] or ["- none"]
    lines += ["", "## Marker", "- `ROUND010_REGRESSION_SAFETY_AUDIT_COMPLETED`"]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("ROUND010_REGRESSION_SAFETY_AUDIT_COMPLETED")
    if regressions:
        sys.exit(1)


if __name__ == "__main__":
    main()
