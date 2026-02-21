"""Artifact existence audit for Round 012 (Gate C — new hard gate).

Scans every team report for `artifact_path:` fields and verifies each file
exists under the workspace root.  A path is considered relative to WORKSPACE_ROOT
unless it starts with '/'.

Exit 0 + ROUND012_ARTIFACT_EXISTENCE_AUDIT_COMPLETED when all paths present.
Exit 1 when any path is missing.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import re
import sys
from pathlib import Path

ROUND_ROOT = Path(__file__).resolve().parents[4]          # …/round-012/
WORKSPACE_ROOT = Path(__file__).resolve().parents[7]      # …/novaic/
REPORTS_DIR = ROUND_ROOT / "20-reports"
OUT_DIR = ROUND_ROOT / "split-close"
OUT_MD = OUT_DIR / "artifact-existence-audit.md"
OUT_JSON = OUT_DIR / "artifact-existence-audit.json"


def _normalise(raw: str) -> str:
    return raw.strip().strip("`")


def extract_artifact_paths(text: str) -> list[str]:
    return [_normalise(m.group(1))
            for m in re.finditer(r"^\s*- artifact_path:[ \t]*(.*)$", text, flags=re.MULTILINE)
            if _normalise(m.group(1))]


def resolve_path(artifact_path: str) -> Path:
    p = Path(artifact_path)
    if p.is_absolute():
        return p
    return WORKSPACE_ROOT / p


def report_snapshot_sha(reports: list[Path]) -> str:
    h = hashlib.sha256()
    for p in sorted(reports, key=lambda x: x.name):
        h.update(p.read_bytes())
    return h.hexdigest()[:16]


def main() -> None:
    reports = sorted(REPORTS_DIR.glob("team-*-report.md"))
    generated_at = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    snap_sha = report_snapshot_sha(reports)

    missing: list[dict] = []
    present: list[dict] = []
    team_results: list[dict] = []

    for report in reports:
        text = report.read_text(encoding="utf-8")
        team = report.stem.replace("-report", "")
        paths = extract_artifact_paths(text)
        team_missing = []
        for ap in paths:
            resolved = resolve_path(ap)
            exists = resolved.exists()
            entry = {"artifact_path": ap, "resolved": str(resolved), "exists": exists}
            if exists:
                present.append({"team": team, **entry})
            else:
                team_missing.append(entry)
                missing.append({"team": team, **entry})
        team_results.append({
            "team": team,
            "paths_checked": len(paths),
            "missing_count": len(team_missing),
            "pass": len(team_missing) == 0,
            "missing": [e["artifact_path"] for e in team_missing],
        })

    gate_pass = len(missing) == 0
    out_json = {
        "round": "round-012",
        "generated_at": generated_at,
        "report_snapshot_sha": snap_sha,
        "workspace_root": str(WORKSPACE_ROOT),
        "paths_checked": len(present) + len(missing),
        "present_count": len(present),
        "missing_count": len(missing),
        "teams": team_results,
        "missing_paths": missing,
        "gate_pass": gate_pass,
        "marker": "ROUND012_ARTIFACT_EXISTENCE_AUDIT_COMPLETED",
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out_json, indent=2), encoding="utf-8")

    lines = [
        "# Round 012 Artifact Existence Audit",
        "",
        "## Metadata",
        f"- generated_at: `{generated_at}`",
        f"- report_snapshot_sha: `{snap_sha}`",
        f"- workspace_root: `{WORKSPACE_ROOT}`",
        "",
        f"- paths_checked: `{len(present) + len(missing)}`",
        f"- present_count: `{len(present)}`",
        f"- missing_count: `{len(missing)}`",
        "",
    ]
    for r in team_results:
        status = "PASS" if r["pass"] else f"FAIL ({r['missing_count']} missing)"
        lines.append(f"- {r['team']}: {r['paths_checked']} paths — {status}")
        for mp in r["missing"]:
            lines.append(f"    ✗ {mp}")
    lines += [
        "",
        "## Summary",
        f"- gate_pass: `{gate_pass}`",
        "",
        "## Marker",
        "- `ROUND012_ARTIFACT_EXISTENCE_AUDIT_COMPLETED`",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("ROUND012_ARTIFACT_EXISTENCE_AUDIT_COMPLETED")
    if not gate_pass:
        sys.exit(1)


if __name__ == "__main__":
    main()
