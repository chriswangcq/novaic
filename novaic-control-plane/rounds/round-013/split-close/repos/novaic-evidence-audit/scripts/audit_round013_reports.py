"""Cross-team evidence audit for Round 013.

Identical field requirements to Round 010:
command + expected_marker + repo_url + commit_sha + migrated_paths + artifact_path.
commit_sha must be full 40-char hex.
repo_url must be in exact canonical set of 7 chriswangcq repos.
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
OUT_MD = OUT_DIR / "cross-team-evidence-audit.md"
OUT_JSON = OUT_DIR / "cross-team-evidence-audit.json"

CANONICAL_REPOS = {
    "https://github.com/chriswangcq/novaic",
    "https://github.com/chriswangcq/novaic-gateway",
    "https://github.com/chriswangcq/novaic-runtime-orchestrator",
    "https://github.com/chriswangcq/novaic-agent-runtime",
    "https://github.com/chriswangcq/novaic-tools-server",
    "https://github.com/chriswangcq/novaic-storage-a",
    "https://github.com/chriswangcq/novaic-storage-b",
}

_COMMAND_PLACEHOLDERS = {"", "command:", "[command]", "your-command-here", "PENDING", "TBD"}
_PLACEHOLDER_RE = re.compile(r"^\[.*\]$|^PENDING$|^TBD$|^N/A$|^\.\.\.$")


def _normalise_url(raw: str) -> str:
    u = raw.strip()
    u = re.sub(r"^-\s+", "", u)
    return u.strip("`").rstrip("/")


def extract_team_status(content: str) -> str:
    m = re.search(r"## Team status\s*\n(?:.*\n)*?- status:[ \t]*(.+)", content, flags=re.MULTILINE)
    return m.group(1).strip().strip("`") if m else ""


def extract_first(field: str, content: str) -> str:
    m = re.search(rf"^\s*- {re.escape(field)}:[ \t]*(.*)$", content, flags=re.MULTILINE)
    return m.group(1).strip() if m else ""


def is_placeholder_command(value: str) -> bool:
    v = value.strip().strip("`")
    return v in _COMMAND_PLACEHOLDERS or not v or bool(_PLACEHOLDER_RE.match(v))


def is_canonical(url: str) -> bool:
    return _normalise_url(url) in CANONICAL_REPOS


def is_full_sha(sha: str) -> bool:
    s = sha.strip().strip("`")
    return bool(re.match(r"^[0-9a-f]{40}$", s, re.IGNORECASE))


def is_placeholder(value: str) -> bool:
    v = value.strip().strip("`")
    return not v or bool(_PLACEHOLDER_RE.match(v))


def report_snapshot_sha(reports: list[Path]) -> str:
    h = hashlib.sha256()
    for p in sorted(reports, key=lambda x: x.name):
        h.update(p.read_bytes())
    return h.hexdigest()[:16]


def main() -> None:
    reports = sorted(REPORTS_DIR.glob("team-*-report.md"))
    generated_at = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    snap_sha = report_snapshot_sha(reports)
    findings: list[dict] = []

    for report in reports:
        text = report.read_text(encoding="utf-8")
        team = report.stem.replace("-report", "")

        status = extract_team_status(text)
        cmd = extract_first("command", text)
        marker = extract_first("expected_marker", text)
        repo_url_raw = next(
            (m.group(1).strip() for m in re.finditer(r"^\s*- repo_url:[ \t]*(.*)$", text, flags=re.MULTILINE)), "")
        commit_sha = extract_first("commit_sha", text)
        migrated_paths = extract_first("migrated_paths", text)
        artifact_path = extract_first("artifact_path", text)

        if status not in {"DONE", "DONE_WITH_GAPS"}:
            findings.append({"team": team, "issue": "team status not DONE", "value": status})
        if is_placeholder_command(cmd):
            findings.append({"team": team, "issue": "missing replayable command", "value": cmd})
        if not marker.strip():
            findings.append({"team": team, "issue": "missing expected_marker", "value": ""})
        if not is_canonical(repo_url_raw):
            findings.append({"team": team, "issue": "repo_url not in canonical set",
                             "value": _normalise_url(repo_url_raw)[:80]})
        if not is_full_sha(commit_sha):
            findings.append({"team": team, "issue": "commit_sha not 40-char hex",
                             "value": commit_sha[:20] or "(empty)"})
        if is_placeholder(migrated_paths):
            findings.append({"team": team, "issue": "missing migrated_paths", "value": migrated_paths})
        if is_placeholder(artifact_path):
            findings.append({"team": team, "issue": "missing artifact_path", "value": artifact_path})

    out_json = {
        "round": "round-013", "generated_at": generated_at, "report_snapshot_sha": snap_sha,
        "reports_scanned": len(reports), "findings_count": len(findings), "findings": findings,
        "marker": "ROUND013_CROSS_TEAM_AUDIT_COMPLETED",
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out_json, indent=2), encoding="utf-8")

    lines = [
        "# Round 013 Cross-Team Evidence Audit", "",
        "## Metadata",
        f"- generated_at: `{generated_at}`",
        f"- report_snapshot_sha: `{snap_sha}`", "",
        "## Policy (Round 013)",
        "- repo_url: exact canonical set (7 repos under chriswangcq)",
        "- Required fields: command + expected_marker + repo_url + commit_sha + migrated_paths + artifact_path", "",
        f"- reports_scanned: `{len(reports)}`",
        f"- findings_count: `{len(findings)}`", "",
    ]
    if findings:
        lines.append("## Fail List")
        for f in findings:
            lines.append(f"- {f['team']}: {f['issue']}")
        lines.append("")
    else:
        lines += ["## Fail List", "- none", ""]
    lines += ["## Marker", "- `ROUND013_CROSS_TEAM_AUDIT_COMPLETED`"]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("ROUND013_CROSS_TEAM_AUDIT_COMPLETED")
    if findings:
        sys.exit(1)


if __name__ == "__main__":
    main()
