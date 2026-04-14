#!/usr/bin/env python3
"""
Reset login password for a user in gateway SQLite (bcrypt), matching /auth/login.

Usage on API host:
  printf 'newSecretPass' | .venv/bin/python scripts/admin_reset_user_password.py user@example.com -
  .venv/bin/python scripts/admin_reset_user_password.py user@example.com 'plain' --db /path/to/gateway.db

Options:
  --db PATH     default: /opt/novaic/data/gateway.db
  --revoke-refresh   delete refresh_tokens rows for this user (force re-login everywhere)
"""
from __future__ import annotations

import argparse
import sqlite3
import sys


def main() -> None:
    p = argparse.ArgumentParser(description="Reset gateway user password_hash (bcrypt)")
    p.add_argument("email", help="User email (matched case-insensitively)")
    p.add_argument(
        "password",
        help="New password, or '-' to read from stdin (no trailing newline required)",
    )
    p.add_argument("--db", default="/opt/novaic/data/gateway.db", help="Path to gateway.db")
    p.add_argument(
        "--revoke-refresh",
        action="store_true",
        help="Remove refresh tokens for this user after password change",
    )
    args = p.parse_args()

    try:
        import bcrypt
    except ImportError:
        print("bcrypt not installed. Use gateway venv: .venv/bin/python ...", file=sys.stderr)
        sys.exit(1)

    if args.password == "-":
        raw = sys.stdin.read()
        password = raw.rstrip("\r\n")
    else:
        password = args.password

    if len(password) < 8:
        print("Password must be at least 8 characters.", file=sys.stderr)
        sys.exit(1)

    email = args.email.lower().strip()
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    conn = sqlite3.connect(args.db)
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE lower(email) = ?", (email,))
        row = cur.fetchone()
        if not row:
            print(f"No user with email {email!r}", file=sys.stderr)
            sys.exit(1)
        user_id = row[0]

        cur.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (hashed, user_id),
        )
        if args.revoke_refresh:
            cur.execute("DELETE FROM refresh_tokens WHERE user_id = ?", (user_id,))
            revoked = cur.rowcount
        else:
            revoked = 0
        conn.commit()
    finally:
        conn.close()

    print(f"OK: password updated for {email} (user_id={user_id})")
    if args.revoke_refresh:
        print(f"OK: revoked {revoked} refresh token row(s)")


if __name__ == "__main__":
    main()
