#!/usr/bin/env python3
"""Lint: scan *_logic.py files for I/O imports.

If a file is named _logic.py, it MUST be a pure function module.
No DB, no HTTP, no file I/O, no network.

Usage:
  python scripts/lint_logic_purity.py [path]
  
Exit code 0 = clean, 1 = violations found.
"""

import ast
import sys
from pathlib import Path

# Imports that indicate I/O — banned in _logic.py files
BANNED_MODULES = {
    # Database
    "sqlite3", "sqlalchemy", "pymongo", "aiosqlite", "databases",
    # HTTP
    "httpx", "requests", "aiohttp", "urllib", "urllib3",
    # File I/O (beyond json/pathlib for pure data)
    "os.path", "shutil", "tempfile",
    # Framework
    "fastapi", "flask", "django", "starlette",
    # Our own I/O layers
    "store", "client", "conn", "session",
}

# Substrings in import paths that indicate I/O
BANNED_SUBSTRINGS = [
    "store", "client", "conn", "session", "db",
    "_actions", "_ports",  # can't import glue or port layer
]


def check_file(path: Path) -> list[str]:
    """Returns list of violations for a _logic.py file."""
    violations = []
    try:
        tree = ast.parse(path.read_text(), filename=str(path))
    except SyntaxError as e:
        return [f"  SyntaxError: {e}"]

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                if name in BANNED_MODULES or any(s in name for s in BANNED_SUBSTRINGS):
                    violations.append(
                        f"  L{node.lineno}: `import {name}` — I/O module banned in _logic.py")

        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module in BANNED_MODULES or any(s in module for s in BANNED_SUBSTRINGS):
                names = ", ".join(a.name for a in node.names)
                violations.append(
                    f"  L{node.lineno}: `from {module} import {names}` — I/O module banned in _logic.py")

    return violations


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    
    # Find all *_logic.py files
    logic_files = sorted(root.rglob("*_logic.py"))
    # Also include logic.py in server/ (our own)
    logic_files += sorted(root.rglob("logic.py"))
    # Exclude venv / node_modules / .git
    logic_files = [f for f in logic_files 
                   if ".venv" not in str(f) and "node_modules" not in str(f) 
                   and ".git" not in str(f) and not f.name.startswith("test_")]
    
    if not logic_files:
        print("No *_logic.py files found.")
        return 0

    total_violations = 0
    for f in logic_files:
        violations = check_file(f)
        if violations:
            print(f"❌ {f}")
            for v in violations:
                print(v)
            total_violations += len(violations)
        else:
            print(f"✅ {f}")

    print(f"\n{'='*40}")
    print(f"Scanned {len(logic_files)} logic files, {total_violations} violations.")
    
    return 1 if total_violations > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
