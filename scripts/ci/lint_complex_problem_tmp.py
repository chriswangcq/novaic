#!/usr/bin/env python3
"""Keep complex-problems durable ledgers free of scratch tmp files."""

from __future__ import annotations

import subprocess
import sys


def main() -> int:
    result = subprocess.run(
        ["git", "ls-files", "-z", ".complex-problems"],
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        sys.stderr.buffer.write(result.stderr)
        return result.returncode

    tracked = [
        path.decode("utf-8", errors="replace")
        for path in result.stdout.split(b"\0")
        if path
    ]
    tmp_paths = [
        path
        for path in tracked
        if path.startswith(".complex-problems/tmp/") or "/tmp/" in path
    ]

    if tmp_paths:
        print("lint_complex_problem_tmp FAILED", file=sys.stderr)
        print(
            ".complex-problems tmp files are scratch artifacts and must not be tracked.",
            file=sys.stderr,
        )
        for path in tmp_paths[:50]:
            print(path, file=sys.stderr)
        if len(tmp_paths) > 50:
            print(f"... {len(tmp_paths) - 50} more", file=sys.stderr)
        return 1

    print("lint_complex_problem_tmp OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
