#!/usr/bin/env python3
"""
存量数据 user_id 归属脚本。

将数据库中 user_id='' 的历史数据归属给指定用户（通常是第一个管理员账号）。

运行前请确保：
  1. Gateway 已启动，admin 用户已通过 POST /auth/register 注册
  2. 已知目标用户的 user_id（从 /auth/me 或 users 表中获取）

用法：
  # 预览（不实际修改，dry-run 默认开启）
  python3 scripts/migrate_user_data.py \\
      --user-id <target_user_id> \\
      --db-path /opt/novaic/data/gateway.db

  # 实际执行
  python3 scripts/migrate_user_data.py \\
      --user-id <target_user_id> \\
      --db-path /opt/novaic/data/gateway.db \\
      --execute

上线顺序：
  Step 1: 部署最新 Gateway（schema v47 已兼容 user_id='' 的旧数据）
  Step 2: 创建 admin 用户：POST /auth/register
  Step 3: 运行本脚本将旧数据归属给 admin
  Step 4: 配置 nginx auth_request（参见 nginx/novaic-cloud.conf）
  Step 5: 重启 Gateway（关闭 DEV_MODE，强制 JWT 校验）
  Step 6: 发布 App 新版本（含登录 UI）
"""
import argparse
import sqlite3
import sys
from datetime import datetime


# 需要归属 user_id 的表和其主键字段
TABLES_WITH_USER_ID = [
    ("agents",   "id"),
    ("api_keys", "id"),
    ("ssh_keys", "id"),
    ("skills",   "id"),
]


def count_empty(conn: sqlite3.Connection, table: str) -> int:
    cur = conn.execute(f"SELECT COUNT(*) FROM {table} WHERE user_id = '' OR user_id IS NULL")
    return cur.fetchone()[0]


def count_empty_config(conn: sqlite3.Connection) -> int:
    cur = conn.execute("SELECT COUNT(*) FROM config WHERE user_id = '' OR user_id IS NULL")
    return cur.fetchone()[0]


def migrate(db_path: str, target_user_id: str, dry_run: bool = True) -> bool:
    if not target_user_id.strip():
        print("ERROR: --user-id cannot be empty", file=sys.stderr)
        return False

    conn = sqlite3.connect(db_path)
    try:
        # 验证目标用户存在
        cur = conn.execute("SELECT id, email, display_name FROM users WHERE id = ?", (target_user_id,))
        row = cur.fetchone()
        if not row:
            print(f"ERROR: User '{target_user_id}' not found in the users table.", file=sys.stderr)
            print("       Please register the user first via POST /auth/register", file=sys.stderr)
            return False

        user_id, email, display_name = row
        print(f"Target user: {display_name or email} ({user_id})")
        print(f"Mode: {'DRY RUN (no changes will be made)' if dry_run else 'EXECUTE (changes will be applied)'}")
        print(f"Database: {db_path}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print()
        print("Rows to migrate:")
        print("-" * 45)

        total = 0

        for table, _pk in TABLES_WITH_USER_ID:
            try:
                n = count_empty(conn, table)
            except sqlite3.OperationalError:
                print(f"  {table:<20} — table not found, skipping")
                continue
            print(f"  {table:<20} {n:>5} rows")
            total += n

        try:
            n_config = count_empty_config(conn)
        except sqlite3.OperationalError:
            n_config = 0
        print(f"  {'config':<20} {n_config:>5} rows")
        total += n_config

        print("-" * 45)
        print(f"  {'TOTAL':<20} {total:>5} rows")
        print()

        if total == 0:
            print("Nothing to migrate. All rows already have a user_id.")
            return True

        if dry_run:
            print("DRY RUN — re-run with --execute to apply changes.")
            return True

        # Confirm before executing
        confirm = input(f"Apply migration? This will update {total} rows. [yes/no]: ").strip().lower()
        if confirm != "yes":
            print("Aborted.")
            return False

        with conn:
            for table, _pk in TABLES_WITH_USER_ID:
                try:
                    conn.execute(
                        f"UPDATE {table} SET user_id = ? WHERE user_id = '' OR user_id IS NULL",
                        (target_user_id,),
                    )
                except sqlite3.OperationalError as e:
                    print(f"  WARNING: Could not update {table}: {e}")

            try:
                conn.execute(
                    "UPDATE config SET user_id = ? WHERE user_id = '' OR user_id IS NULL",
                    (target_user_id,),
                )
            except sqlite3.OperationalError as e:
                print(f"  WARNING: Could not update config: {e}")

        print(f"DONE — Migrated {total} rows to user_id={target_user_id}")
        return True

    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Migrate legacy user_id='' rows to a specific user.",
    )
    parser.add_argument("--user-id", required=True, help="Target user_id (UUID from users table)")
    parser.add_argument("--db-path", default="gateway.db", help="Path to gateway.db (default: ./gateway.db)")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually apply changes (omit for dry-run preview)",
    )
    args = parser.parse_args()

    ok = migrate(args.db_path, args.user_id, dry_run=not args.execute)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
