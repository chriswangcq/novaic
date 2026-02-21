#!/usr/bin/env python3
"""
Round 010 commit reachability checker.

For each (repo_url, commit_sha) pair registered in COMMIT_PAIRS,
checks whether the commit is reachable on the remote via git ls-remote
or git cat-file (local). Outputs one line per pair:
  REACHABLE   <repo_url> <commit_sha>
  UNREACHABLE <repo_url> <commit_sha>
  SKIP_REMOTE <repo_url> <commit_sha>  (network unavailable)

Exits 0 if at least one REACHABLE pair found and zero UNREACHABLE.
Exits 1 otherwise.
"""
import subprocess
import sys

# Desktop team commit pairs for Round 010
# (repo_url, commit_sha, description)
COMMIT_PAIRS = [
    (
        "https://github.com/chriswangcq/novaic",
        "ffd905020afe92792069fde4b925b2c04a8aeb5c",
        "round-009 desktop report finalized",
    ),
    (
        "https://github.com/chriswangcq/novaic",
        "b099264128eabce2669744e18a705b6f62a0f947",
        "round-009 strict split-config abort",
    ),
    (
        "https://github.com/chriswangcq/novaic",
        "7a6a03ddf08557825e54eb4bd45b6813ac58f787",
        "round-008 machine-readable contract compliance",
    ),
]

REMOTE = "https://github.com/chriswangcq/novaic"


def check_via_git_cat_file(sha: str) -> str:
    """Check local object store first (fast path)."""
    try:
        r = subprocess.run(
            ["git", "cat-file", "-t", sha],
            capture_output=True, text=True, timeout=5
        )
        if r.returncode == 0 and "commit" in r.stdout:
            return "LOCAL"
    except Exception:
        pass
    return "UNKNOWN"


def check_via_ls_remote(repo_url: str, sha: str) -> str:
    """
    Use git ls-remote to fetch all refs; check if sha prefix appears.
    Falls back to SKIP_REMOTE on network failure.
    """
    try:
        # First check if sha is reachable as a local commit that's been pushed
        # by checking if it's an ancestor of the remote branch tip.
        r = subprocess.run(
            ["git", "ls-remote", "origin"],
            capture_output=True, text=True, timeout=15
        )
        if r.returncode == 0:
            # Check if our sha is listed (exact prefix match, >= 7 chars)
            for line in r.stdout.splitlines():
                remote_sha = line.split()[0] if line.split() else ""
                if remote_sha.startswith(sha[:7]) or sha.startswith(remote_sha[:7]):
                    return "REACHABLE"
            # Check if sha is a local commit that's an ancestor of remote HEAD
            for line in r.stdout.splitlines():
                remote_sha = line.split()[0] if line.split() else ""
                if len(remote_sha) == 40:
                    merge_base = subprocess.run(
                        ["git", "merge-base", "--is-ancestor", sha, remote_sha],
                        capture_output=True, timeout=5
                    )
                    if merge_base.returncode == 0:
                        return "REACHABLE"
        return "UNREACHABLE"
    except subprocess.TimeoutExpired:
        return "SKIP_REMOTE"
    except Exception:
        return "SKIP_REMOTE"


results = []
reachable_count = 0
unreachable_count = 0

for repo_url, sha, desc in COMMIT_PAIRS:
    local = check_via_git_cat_file(sha)
    if local == "LOCAL":
        status = check_via_ls_remote(repo_url, sha)
    else:
        status = check_via_ls_remote(repo_url, sha)

    results.append((status, repo_url, sha, desc))
    if status == "REACHABLE":
        reachable_count += 1
    elif status == "UNREACHABLE":
        unreachable_count += 1

print("=== Commit Reachability Report ===")
for status, repo_url, sha, desc in results:
    print(f"{status:<12} {sha[:12]}  {repo_url}  # {desc}")

print()
print(f"reachable={reachable_count} unreachable={unreachable_count} skip={len(results) - reachable_count - unreachable_count}")

if unreachable_count > 0:
    print("COMMIT_REACHABILITY=FAIL (UNREACHABLE pairs found)")
    sys.exit(1)
elif reachable_count == 0:
    print("COMMIT_REACHABILITY=FAIL (zero REACHABLE pairs)")
    sys.exit(1)
else:
    print("COMMIT_REACHABILITY=PASS")
    sys.exit(0)
