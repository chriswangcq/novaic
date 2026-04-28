#!/usr/bin/env python3
"""
Canary traffic generator for PR-17 subscriber rollout.

Usage (run on the production host, or via SSH with port-forward to 19998):

  # 1. Bootstrap the canary user + agent (idempotent; run once per fresh DB)
  python3 traffic.py bootstrap

  # 2. Send N messages at given TPS to exercise outbox → subscriber path
  python3 traffic.py send --count 100 --tps 10

  # 3. Observe outbox state (delivery lag, failures, backlog)
  python3 traffic.py observe

  # 4. One-shot: print a formatted Canary stage summary (5 min watch)
  python3 traffic.py watch --duration 300

What it exercises
-----------------
`send` posts to `/internal/entities/messages/action/send`, which invokes
`message_actions.send_action(...)`. That write goes through Entangled's
`SqlEntityStore.append()`:
  * outbox row is written co-transactionally
  * DispatchSubscriber claims the outbox row and dispatches to Queue

If everything is healthy:
  * `observe` shows no backlog older than ~5 s and `permanent_failed` == 0
  * Queue logs show exactly 1 subscriber dispatch per message

If the system is broken (duplicate send, FK mismatch, orphan messages, etc),
the outbox accumulates rows, `attempts` grows, or `permanent_failed` > 0.

Safety
------
* This script uses the `internal/entities` endpoints which have NO auth on Business.
  For that reason it must connect ONLY to 127.0.0.1:19998 (production binds Business
  to localhost). Never expose Business port 19998 to the internet.
* The canary user (`canary_u_1`) is a permanent fixture. Do not delete in prod.
* `send` is rate-limited by `--tps`; default 10 to avoid accidental flood.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sqlite3
import sys
import time
import uuid
from typing import Any

import httpx

# ── Constants ────────────────────────────────────────────────────────────────

BUSINESS_URL = os.environ.get("CANARY_BUSINESS_URL", "http://127.0.0.1:19998")
ENTANGLED_DB = os.environ.get("CANARY_ENTANGLED_DB", "/opt/novaic/data/entangled.db")
# CANARY_AGENT_ID / CANARY_USER_ID / NAME env overrides let smoke
# scripts target separate canary agents without forking this traffic
# helper. The defaults preserve the PR-17 subscriber canary behavior.
CANARY_USER_ID = os.environ.get("CANARY_USER_ID", "canary_u_1")
CANARY_AGENT_ID = os.environ.get("CANARY_AGENT_ID", "canary_a_1")
CANARY_AGENT_NAME = os.environ.get("CANARY_AGENT_NAME", "Canary Observation Agent")


# ── Helpers ──────────────────────────────────────────────────────────────────

def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())


async def _post_json(client: httpx.AsyncClient, path: str, body: dict, params: dict | None = None) -> httpx.Response:
    url = f"{BUSINESS_URL}{path}"
    r = await client.post(url, json=body, params=params, timeout=10.0)
    return r


# ── bootstrap ────────────────────────────────────────────────────────────────

async def bootstrap() -> int:
    """Ensure canary_u_1 agent exists. Idempotent (safe to re-run).

    We skip writing a row to the `users` table because:
      1. In this architecture the `users` table lives in Gateway's gateway.db
         (AuthEntityStore), not in Entangled's entangled.db.
      2. Entangled doesn't enforce FK (no `PRAGMA foreign_keys=ON`), so
         `agents.user_id = 'canary_u_1'` is accepted even without a users row.
      3. `AgentOwnershipResolver` only reads `agents.user_id`; it never JOINs.

    So bootstrap is: create-or-upsert one `agents` row with a known id.
    """
    async with httpx.AsyncClient() as client:
        r = await _post_json(
            client,
            "/internal/entities/agents",
            body={
                "id": CANARY_AGENT_ID,
                "name": CANARY_AGENT_NAME,
                "setup_complete": True,
                "model_id": "canary",
            },
            params={"user_id": CANARY_USER_ID, "notify": "false"},
        )
        if r.status_code >= 400 and "exist" not in r.text.lower() and "UNIQUE" not in r.text:
            # Upsert path — agent may already exist from a previous run
            r2 = await client.put(
                f"{BUSINESS_URL}/internal/entities/agents/{CANARY_AGENT_ID}",
                json={
                    "id": CANARY_AGENT_ID,
                    "name": CANARY_AGENT_NAME,
                    "setup_complete": True,
                    "model_id": "canary",
                },
                params={"user_id": CANARY_USER_ID, "notify": "false"},
                timeout=10.0,
            )
            r2.raise_for_status()
            print(f"[{_now_iso()}] bootstrap: upserted agent {CANARY_AGENT_ID}")
        else:
            print(f"[{_now_iso()}] bootstrap: created/idempotent agent {CANARY_AGENT_ID} user={CANARY_USER_ID} status={r.status_code}")

    # Sanity: verify ownership endpoint returns what we expect.
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{BUSINESS_URL}/internal/agents/{CANARY_AGENT_ID}/owner",
            timeout=10.0,
        )
        if r.status_code != 200:
            print(f"[{_now_iso()}] bootstrap: ERROR owner-lookup failed status={r.status_code} body={r.text[:200]}")
            return 2
        data = r.json()
        if data.get("user_id") != CANARY_USER_ID:
            print(f"[{_now_iso()}] bootstrap: ERROR owner mismatch got={data} expected={CANARY_USER_ID}")
            return 2
        print(f"[{_now_iso()}] bootstrap: owner-lookup OK {data}")

    return 0


# ── send ─────────────────────────────────────────────────────────────────────

async def _send_one(client: httpx.AsyncClient, idx: int) -> tuple[int, str]:
    """Send one USER_MESSAGE via the action hook, which exercises inline dispatch."""
    msg_id = f"canary-{uuid.uuid4().hex[:12]}"
    # Payload shape required by business.message_actions.send_action:
    #   payload["message"]  : str  (non-empty; checked at line 82 of message_actions.py)
    #   payload["agent_id"] : str  (or pulled from params)
    body = {
        "user_id": CANARY_USER_ID,
        "params": {"agent_id": CANARY_AGENT_ID},
        "payload": {
            "agent_id": CANARY_AGENT_ID,
            "message": f"canary ping #{idx} at {_now_iso()} ({msg_id})",
        },
    }
    r = await _post_json(client, "/internal/entities/messages/action/send", body=body)
    return r.status_code, msg_id


async def send(count: int, tps: int, concurrency: int) -> int:
    """Send `count` messages at `tps` requests/sec with `concurrency` in flight."""
    if tps <= 0 or count <= 0:
        print("ERROR: count and tps must be positive", file=sys.stderr)
        return 2

    print(f"[{_now_iso()}] send: count={count} tps={tps} concurrency={concurrency} target={BUSINESS_URL}")
    interval = 1.0 / tps
    ok = 0
    fail = 0
    start = time.monotonic()

    sem = asyncio.Semaphore(concurrency)

    async with httpx.AsyncClient() as client:
        async def _task(i: int) -> None:
            nonlocal ok, fail
            async with sem:
                try:
                    status, mid = await _send_one(client, i)
                    if 200 <= status < 300:
                        ok += 1
                    else:
                        fail += 1
                        if fail <= 5:
                            print(f"  fail idx={i} status={status}")
                except Exception as e:
                    fail += 1
                    if fail <= 5:
                        print(f"  fail idx={i} exc={type(e).__name__}: {e}")

        tasks = []
        for i in range(count):
            tasks.append(asyncio.create_task(_task(i)))
            await asyncio.sleep(interval)
        await asyncio.gather(*tasks)

    elapsed = time.monotonic() - start
    print(f"[{_now_iso()}] send: done ok={ok} fail={fail} elapsed={elapsed:.2f}s "
          f"effective_tps={count/elapsed:.1f}")
    return 0 if fail == 0 else 1


# ── observe ──────────────────────────────────────────────────────────────────

def _outbox_stats(db_path: str) -> dict[str, Any]:
    """Read outbox-level stats directly from SQLite (read-only, WAL-safe)."""
    uri = f"file:{db_path}?mode=ro"
    con = sqlite3.connect(uri, uri=True, timeout=5.0)
    con.row_factory = sqlite3.Row
    try:
        # Schema check
        row = con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='message_outbox'"
        ).fetchone()
        if not row:
            return {"schema_exists": False}

        out: dict[str, Any] = {"schema_exists": True}
        out["total"] = con.execute("SELECT COUNT(*) FROM message_outbox").fetchone()[0]
        out["pending"] = con.execute(
            "SELECT COUNT(*) FROM message_outbox WHERE delivered_at IS NULL"
        ).fetchone()[0]
        out["delivered"] = con.execute(
            "SELECT COUNT(*) FROM message_outbox WHERE delivered_at IS NOT NULL"
        ).fetchone()[0]
        out["locked"] = con.execute(
            "SELECT COUNT(*) FROM message_outbox "
            "WHERE delivered_at IS NULL AND locked_until IS NOT NULL "
            "AND locked_until > (strftime('%s','now')*1000)"
        ).fetchone()[0]

        # Oldest pending (lag in seconds)
        lag_row = con.execute(
            "SELECT MIN(created_at) FROM message_outbox WHERE delivered_at IS NULL"
        ).fetchone()
        oldest_created = lag_row[0] if lag_row and lag_row[0] else None
        if oldest_created:
            try:
                # created_at is TIMESTAMP; try epoch form first, else treat as ISO string
                oldest_ts: float
                if isinstance(oldest_created, (int, float)):
                    oldest_ts = float(oldest_created)
                    if oldest_ts > 1e12:  # ms
                        oldest_ts /= 1000
                else:
                    # sqlite CURRENT_TIMESTAMP format: "YYYY-MM-DD HH:MM:SS"
                    oldest_ts = time.mktime(time.strptime(str(oldest_created), "%Y-%m-%d %H:%M:%S"))
                out["oldest_pending_age_sec"] = round(time.time() - oldest_ts, 1)
            except (ValueError, TypeError):
                out["oldest_pending_age_sec"] = f"parse-error({oldest_created!r})"
        else:
            out["oldest_pending_age_sec"] = 0

        # Retry stats: retrying = pending with non-zero attempts that
        # still have budget; permanent_failed = flagged dead-letters.
        out["retrying"] = con.execute(
            "SELECT COUNT(*) FROM message_outbox "
            "WHERE delivered_at IS NULL AND attempts > 0 "
            "  AND permanent_failure = 0"
        ).fetchone()[0]
        out["permanent_failed"] = con.execute(
            "SELECT COUNT(*) FROM message_outbox "
            "WHERE delivered_at IS NULL AND permanent_failure = 1"
        ).fetchone()[0]

        # By trigger type
        out["by_trigger"] = {
            r["trigger_type"]: r["n"]
            for r in con.execute(
                "SELECT trigger_type, COUNT(*) AS n FROM message_outbox GROUP BY trigger_type"
            ).fetchall()
        }

        return out
    finally:
        con.close()


def observe() -> int:
    """Snapshot the outbox state and print a human-friendly summary."""
    print(f"[{_now_iso()}] observe: reading {ENTANGLED_DB}")
    try:
        s = _outbox_stats(ENTANGLED_DB)
    except sqlite3.OperationalError as e:
        print(f"  ERROR: cannot open DB: {e}", file=sys.stderr)
        return 2

    if not s.get("schema_exists"):
        print("  schema: message_outbox TABLE DOES NOT EXIST")
        print("  → Entangled has not run the PR-14 ensure_schema path on this DB.")
        print("  → Check Entangled startup logs; make sure PR-14 code is deployed.")
        return 3

    print(f"  total              = {s['total']}")
    print(f"  pending            = {s['pending']}  (locked={s['locked']})")
    print(f"  delivered          = {s['delivered']}")
    print(f"  retrying           = {s['retrying']}  (attempts>0, not poisoned)")
    print(f"  poisoned           = {s['poisoned']}  (permanent failures, need manual attention)")
    print(f"  oldest_pending_age = {s['oldest_pending_age_sec']}s")
    print(f"  by_trigger         = {json.dumps(s['by_trigger'], ensure_ascii=False)}")

    # Simple health judgement
    status = "OK"
    if s["poisoned"] > 0:
        status = "WARN (poisoned rows exist)"
    if isinstance(s["oldest_pending_age_sec"], (int, float)) and s["oldest_pending_age_sec"] > 30:
        status = f"WARN (backlog: oldest_pending_age={s['oldest_pending_age_sec']}s > 30s)"
    print(f"  verdict            = {status}")
    return 0 if status == "OK" else 1


# ── watch ────────────────────────────────────────────────────────────────────

async def watch(duration: int, interval: int) -> int:
    """Poll observe() every `interval` seconds for `duration` seconds."""
    end = time.monotonic() + duration
    while time.monotonic() < end:
        observe()
        print("---")
        await asyncio.sleep(interval)
    return 0


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> int:
    p = argparse.ArgumentParser(description="Canary traffic + observer for PR-17")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("bootstrap", help="Create canary user + agent (idempotent)")

    p_send = sub.add_parser("send", help="Send USER_MESSAGE canary traffic")
    p_send.add_argument("--count", type=int, default=10, help="Total messages to send")
    p_send.add_argument("--tps", type=int, default=10, help="Target requests per second")
    p_send.add_argument("--concurrency", type=int, default=5, help="Concurrent in-flight requests")

    sub.add_parser("observe", help="Print a snapshot of outbox state")

    p_watch = sub.add_parser("watch", help="Periodic observe loop")
    p_watch.add_argument("--duration", type=int, default=300, help="Total seconds to watch")
    p_watch.add_argument("--interval", type=int, default=15, help="Poll interval seconds")

    args = p.parse_args()

    if args.cmd == "bootstrap":
        return asyncio.run(bootstrap())
    if args.cmd == "send":
        return asyncio.run(send(args.count, args.tps, args.concurrency))
    if args.cmd == "observe":
        return observe()
    if args.cmd == "watch":
        return asyncio.run(watch(args.duration, args.interval))

    p.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
