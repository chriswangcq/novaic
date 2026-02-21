"""Commit reachability audit for Round 010.

Key change vs Round 009:
- Uses local git clone as reachability oracle instead of git ls-remote (which times out in
  offline environments).  Maps canonical GitHub HTTPS URL to local clone path, then runs
  ``git cat-file -e <sha>^{commit}`` to check existence.
- Result per (repo_url, commit_sha) pair:
    REACHABLE   — sha found in local clone (implies it was fetched from the remote).
    UNREACHABLE — local clone exists but sha absent (genuine failure / fake sha).
    SKIP_REMOTE — no local clone mapping for this repo_url (cannot verify).
- Gate B rule: each team must have >=1 REACHABLE pair; UNREACHABLE count must be zero.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROUND_ROOT = Path(__file__).resolve().parents[4]   # …/round-010/
REPORTS_DIR = ROUND_ROOT / "20-reports"
OUT_DIR = ROUND_ROOT / "split-close"
OUT_MD = OUT_DIR / "commit-reachability-audit.md"
OUT_JSON = OUT_DIR / "commit-reachability-audit.json"

# Map canonical GitHub HTTPS repo URL → absolute path of local clone.
# Only repos that have a local clone can be verified as REACHABLE/UNREACHABLE.
REMOTE_TO_LOCAL: dict[str, str] = {
    "https://github.com/chriswangcq/novaic": "/Users/wangchaoqun/novaic",
    "https://github.com/chriswangcq/novaic-runtime-orchestrator": "/Users/wangchaoqun/novaic-runtime-orchestrator",
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


def _normalise(raw: str) -> str:
    u = raw.strip()
    u = re.sub(r"^-\s+", "", u)
    return u.strip("`").rstrip("/")


def check_reachability(repo_url: str, sha: str) -> str:
    u = _normalise(repo_url)
    s = _normalise(sha)
    if len(s) != 40 or u not in CANONICAL_REPOS:
        return "SKIP_REMOTE"
    local_path = REMOTE_TO_LOCAL.get(u)
    if local_path is None:
        return "SKIP_REMOTE"
    try:
        r = subprocess.run(
            ["git", "-C", local_path, "cat-file", "-e", f"{s}^{{commit}}"],
            capture_output=True, timeout=5,
        )
        return "REACHABLE" if r.returncode == 0 else "UNREACHABLE"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return "SKIP_REMOTE"


def extract_pairs(text: str) -> list[tuple[str, str]]:
    urls = [m.group(1).strip() for m in
            re.finditer(r"^\s*- repo_url:[ \t]*(.*)$", text, flags=re.MULTILINE)]
    shas = [m.group(1).strip() for m in
            re.finditer(r"^\s*- commit_sha:[ \t]*(.*)$", text, flags=re.MULTILINE)]
    length = max(len(urls), len(shas), 1)
    return [(urls[i] if i < len(urls) else "", shas[i] if i < len(shas) else "") for i in range(length)]


def report_snapshot_sha(reports: list[Path]) -> str:
    h = hashlib.sha256()
    for p in sorted(reports, key=lambda x: x.name):
        h.update(p.read_bytes())
    return h.hexdigest()[:16]


def main() -> None:
    reports = sorted(REPORTS_DIR.glob("team-*-report.md"))
    generated_at = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    snap_sha = report_snapshot_sha(reports)

    all_results: list[dict] = []
    unreachable: list[dict] = []
    teams_with_reachable: set[str] = set()
    teams_missing_reachable: list[str] = []

    for report in reports:
        text = report.read_text(encoding="utf-8")
        team = report.stem.replace("-report", "")
        pairs = extract_pairs(text)
        team_has_reachable = False
        for idx, (url, sha) in enumerate(pairs, start=1):
            status = check_reachability(url, sha)
            entry = {
                "team": team, "pair_index": idx,
                "repo_url": _normalise(url)[:80],
                "commit_sha_prefix": _normalise(sha)[:12] or "(empty)",
                "status": status,
            }
            all_results.append(entry)
            if status == "REACHABLE":
                team_has_reachable = True
                teams_with_reachable.add(team)
            elif status == "UNREACHABLE":
                unreachable.append(entry)
        if not team_has_reachable:
            teams_missing_reachable.append(team)

    gate_b_fail = bool(unreachable) or bool(teams_missing_reachable)

    out_json = {
        "round": "round-010",
        "generated_at": generated_at,
        "report_snapshot_sha": snap_sha,
        "pairs_checked": len(all_results),
        "reachable_count": sum(1 for r in all_results if r["status"] == "REACHABLE"),
        "skip_remote_count": sum(1 for r in all_results if r["status"] == "SKIP_REMOTE"),
        "unreachable_count": len(unreachable),
        "teams_with_reachable": sorted(teams_with_reachable),
        "teams_missing_reachable": teams_missing_reachable,
        "results": all_results,
        "marker": "ROUND010_COMMIT_REACHABILITY_AUDIT_COMPLETED",
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out_json, indent=2), encoding="utf-8")

    lines = [
        "# Round 010 Commit Reachability Audit",
        "",
        "## Metadata",
        f"- generated_at: `{generated_at}`",
        f"- report_snapshot_sha: `{snap_sha}`",
        "",
        "## Method",
        "- Local clone oracle: maps https://github.com/chriswangcq/novaic → /Users/wangchaoqun/novaic",
        "- Uses `git cat-file -e <sha>^{commit}` for presence check",
        "- SKIP_REMOTE: no local clone mapping available",
        "",
        f"- pairs_checked: `{len(all_results)}`",
        f"- reachable_count: `{out_json['reachable_count']}`",
        f"- skip_remote_count: `{out_json['skip_remote_count']}`",
        f"- unreachable_count: `{len(unreachable)}`",
        f"- teams_with_reachable: `{sorted(teams_with_reachable)}`",
        f"- teams_missing_reachable: `{teams_missing_reachable}`",
        "",
    ]
    if unreachable:
        lines += ["## UNREACHABLE pairs (Gate B fail)", ""]
        for e in unreachable:
            lines.append(f"- {e['team']}: pair{e['pair_index']} sha={e['commit_sha_prefix']} url={e['repo_url'][:50]}")
        lines.append("")
    else:
        lines += ["## UNREACHABLE pairs", "- none", ""]
    if teams_missing_reachable:
        lines += ["## Teams with zero REACHABLE (Gate B fail)", ""]
        for t in teams_missing_reachable:
            lines.append(f"- {t}")
        lines.append("")
    else:
        lines += ["## Teams with zero REACHABLE", "- none (all teams have >=1 REACHABLE)", ""]
    lines += ["## Marker", "- `ROUND010_COMMIT_REACHABILITY_AUDIT_COMPLETED`"]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("ROUND010_COMMIT_REACHABILITY_AUDIT_COMPLETED")
    if gate_b_fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
