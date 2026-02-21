"""Canonical repo_url enforcement for Round 010.

Policy: repo_url must be exactly one of the 7 approved https://github.com/chriswangcq/<repo>
URLs.  file:/// and local: are unconditionally rejected.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import re
import sys
from pathlib import Path

ROUND_ROOT = Path(__file__).resolve().parents[4]
REPORTS_DIR = ROUND_ROOT / "20-reports"
OUT_DIR = ROUND_ROOT / "split-close"
OUT_MD = OUT_DIR / "canonical-repo-url-audit.md"
OUT_JSON = OUT_DIR / "canonical-repo-url-audit.json"

CANONICAL_REPOS = {
    "https://github.com/chriswangcq/novaic",
    "https://github.com/chriswangcq/novaic-gateway",
    "https://github.com/chriswangcq/novaic-runtime-orchestrator",
    "https://github.com/chriswangcq/novaic-agent-runtime",
    "https://github.com/chriswangcq/novaic-tools-server",
    "https://github.com/chriswangcq/novaic-storage-a",
    "https://github.com/chriswangcq/novaic-storage-b",
}


def _normalise(raw: str) -> str:
    u = raw.strip()
    u = re.sub(r"^-\s+", "", u)
    return u.strip("`").rstrip("/")


def is_canonical(raw: str) -> bool:
    return _normalise(raw) in CANONICAL_REPOS


def extract_repo_urls(text: str) -> list[str]:
    return [m.group(1).strip() for m in
            re.finditer(r"^\s*- repo_url:[ \t]*(.*)$", text, flags=re.MULTILINE)]


def report_snapshot_sha(reports: list[Path]) -> str:
    h = hashlib.sha256()
    for p in sorted(reports, key=lambda x: x.name):
        h.update(p.read_bytes())
    return h.hexdigest()[:16]


def main() -> None:
    reports = sorted(REPORTS_DIR.glob("team-*-report.md"))
    generated_at = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    snap_sha = report_snapshot_sha(reports)

    violations: list[dict] = []
    team_results: list[dict] = []

    for report in reports:
        text = report.read_text(encoding="utf-8")
        team = report.stem.replace("-report", "")
        urls = extract_repo_urls(text)
        bad = [_normalise(u) for u in urls if not is_canonical(u)]
        team_results.append({
            "team": team,
            "urls_checked": len(urls),
            "violations": bad,
            "pass": len(bad) == 0,
        })
        for b in bad:
            violations.append({"team": team, "url": b[:80]})

    gate_pass = len(violations) == 0
    out_json = {
        "round": "round-010",
        "generated_at": generated_at,
        "report_snapshot_sha": snap_sha,
        "teams": team_results,
        "violation_count": len(violations),
        "violations": violations,
        "gate_pass": gate_pass,
        "marker": "ROUND010_CANONICAL_REPO_URL_AUDIT_COMPLETED",
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out_json, indent=2), encoding="utf-8")

    lines = [
        "# Round 010 Canonical Repo URL Audit",
        "",
        "## Metadata",
        f"- generated_at: `{generated_at}`",
        f"- report_snapshot_sha: `{snap_sha}`",
        "",
        "## Policy",
        "- Allowed: https://github.com/chriswangcq/{novaic,novaic-gateway,novaic-runtime-orchestrator,novaic-agent-runtime,novaic-tools-server,novaic-storage-a,novaic-storage-b}",
        "- Rejected: file:///, local:, ssh, any other",
        "",
    ]
    for r in team_results:
        status = "PASS" if r["pass"] else f"FAIL ({len(r['violations'])} violations)"
        lines.append(f"- {r['team']}: {r['urls_checked']} urls checked — {status}")
        for v in r["violations"]:
            lines.append(f"    ✗ {v[:70]!r}")
    lines += [
        "",
        "## Summary",
        f"- violation_count: `{len(violations)}`",
        f"- gate_pass: `{gate_pass}`",
        "",
        "## Marker",
        "- `ROUND010_CANONICAL_REPO_URL_AUDIT_COMPLETED`",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("ROUND010_CANONICAL_REPO_URL_AUDIT_COMPLETED")
    if not gate_pass:
        sys.exit(1)


if __name__ == "__main__":
    main()
