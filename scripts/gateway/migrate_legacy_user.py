#!/usr/bin/env python3
"""
将老数据（user_id = ''）迁移到指定用户 ID。

用法：
    # 预览将要迁移的数量（不修改数据库）
    python scripts/migrate_legacy_user.py --user-id alice@example.com

    # 实际执行迁移
    python scripts/migrate_legacy_user.py --user-id alice@example.com --apply

    # 指定自定义数据库路径
    python scripts/migrate_legacy_user.py --user-id alice@example.com --db /opt/novaic/data/gateway.db --apply

涉及的表：agents / api_keys / ssh_keys / skills / config
config 表使用复合主键 (user_id, key)，采用 INSERT OR REPLACE 处理冲突。
"""
import argparse
import sqlite3
import sys
from pathlib import Path

DEFAULT_DB = Path.home() / ".novaic" / "gateway.db"

SIMPLE_TABLES = ["agents", "api_keys", "ssh_keys", "skills"]


def count_legacy_rows(conn: sqlite3.Connection) -> dict:
    """统计各表 user_id='' 的存量行数。"""
    counts = {}
    for table in SIMPLE_TABLES + ["config"]:
        row = conn.execute(f"SELECT COUNT(*) FROM {table} WHERE user_id = ''").fetchone()
        counts[table] = row[0]
    return counts


def migrate(conn: sqlite3.Connection, user_id: str) -> dict:
    """
    将所有 user_id='' 的数据迁移到 user_id。

    config 表单独处理：因为 (user_id, key) 是复合主键，
    先用 INSERT OR REPLACE 将行以新 user_id 插入（覆盖目标用户已有同名 key），
    再删除原始的 user_id='' 行。
    """
    affected = {}

    for table in SIMPLE_TABLES:
        cur = conn.execute(
            f"UPDATE {table} SET user_id = ? WHERE user_id = ''",
            (user_id,),
        )
        affected[table] = cur.rowcount

    # config 表：复合主键处理
    old_rows = conn.execute(
        "SELECT key, value, updated_at FROM config WHERE user_id = ''"
    ).fetchall()

    inserted = 0
    for key, value, updated_at in old_rows:
        conn.execute(
            """INSERT OR REPLACE INTO config (user_id, key, value, updated_at)
               VALUES (?, ?, ?, ?)""",
            (user_id, key, value, updated_at),
        )
        inserted += 1

    conn.execute("DELETE FROM config WHERE user_id = ''")
    affected["config"] = inserted

    return affected


def main():
    parser = argparse.ArgumentParser(description="将老数据迁移到指定用户 ID")
    parser.add_argument("--user-id", required=True, help="目标用户 ID（e.g. alice@example.com）")
    parser.add_argument(
        "--db",
        default=str(DEFAULT_DB),
        help=f"数据库路径（默认：{DEFAULT_DB}）",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="实际执行迁移（不加此参数只预览）",
    )
    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"[ERROR] 数据库文件不存在：{db_path}", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    try:
        print(f"\n数据库：{db_path}")
        print(f"目标用户：{args.user_id}")
        print(f"模式：{'执行迁移' if args.apply else '预览（dry-run）'}\n")

        counts = count_legacy_rows(conn)

        total = sum(counts.values())
        if total == 0:
            print("✓ 没有需要迁移的存量数据（user_id='' 行数为 0）。")
            return

        print("存量数据（user_id='' 的行数）：")
        for table, n in counts.items():
            print(f"  {table:<15} {n} 行")
        print(f"  {'合计':<15} {total} 行")

        if not args.apply:
            print("\n[预览模式] 未作任何修改。加 --apply 执行迁移。")
            return

        # 实际执行
        conn.execute("BEGIN EXCLUSIVE")
        try:
            affected = migrate(conn, args.user_id)
            conn.execute("COMMIT")
        except Exception as e:
            conn.execute("ROLLBACK")
            print(f"\n[ERROR] 迁移失败，已回滚：{e}", file=sys.stderr)
            sys.exit(1)

        print("\n迁移结果：")
        for table, n in affected.items():
            print(f"  {table:<15} {n} 行 → user_id='{args.user_id}'")

        # 验证
        remaining = count_legacy_rows(conn)
        leftover = sum(remaining.values())
        if leftover == 0:
            print(f"\n✓ 迁移成功，无残留 user_id='' 数据。")
        else:
            print(f"\n[WARN] 仍有 {leftover} 行 user_id='' 残留，请检查。")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
