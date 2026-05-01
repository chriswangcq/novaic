# Runbook: Subscriber Canary (PR-17)

> **TD-5 (2026-04-15) UPDATE — edit the overlay, NOT services.json**
>
> The canary flip lives at `/opt/novaic/etc/runtime_switches.json` — a file
> outside `/opt/novaic/services` that `rsync -azL --delete` cannot touch.
> `common/strict_config.py` deep-merges it on top of the committed
> `services.json` defaults at process startup.
>
> ```json
> {
>   "subscriber_enabled": true,
>   "health_check_interval_seconds": 5,
>   "scheduler_poll_interval_seconds": 1.0
> }
> ```
>
> Verify:
>
> ```bash
> grep "runtime_switches=" /opt/novaic/data/logs/business-$(date +%Y%m%d).log | head -1
> ```
>
> **Do not edit** `/opt/novaic/services/novaic-common/config/services.json`
> (or its sibling copies under `novaic-gateway` / `novaic-agent-runtime`).
> The overlay wins, and the next `deploy-business.sh` run will rsync your
> edit away anyway — this is exactly the failure mode TD-5 was born to
> eliminate (PR-33 §C.2.2). Unknown keys in the overlay crash startup with
> `ConfigError: unknown key(s)` — typos are loud, not silent.
>
> Every `main_*.py` emits a `ServiceConfig: runtime_switches={...}` INFO
> line at lifespan init — that is the single audit target for "what
> switches is this process actually running with?". If you see a leftover
> `export NOVAIC_*` line or a raw `services.json` jq-edit during an
> incident, it is a stale clone — grep and fix.

> **RED LINE — READ BEFORE TOUCHING PROD**
>
> This is NOT a small feature rollout. The target production environment is
> running **pre-PR-15** code. Enabling the subscriber deploys the entire
> PR-04 … PR-16 stack to production for the first time, including:
>
> * Internal caller headers (PR-05 / PR-06)
> * `AgentOwnershipResolver` + TTL cache (PR-07 / PR-08)
> * `TriggerType` enum + migration (PR-09)
> * `DispatchAssembler` (PR-10)
> * Business `_dispatch_trigger` → Assembler shim (PR-11)
> * HealthWorker + Scheduler async rewrite (PR-12 / PR-13)
> * Entangled `message_outbox` schema + co-transactional write (PR-14)
> * DispatchSubscriber skeleton (PR-15)
> * DispatchSubscriber full implementation (PR-16)
>
> Therefore Canary observation windows are **4–6 hours** per stage, NOT 30 min.
> If anything smells off — stop and rollback. This runbook includes both
> fast-path and cold-path rollback procedures.

---

## Overview

**Goal** — Turn on `DispatchSubscriber` in production alongside the legacy
inline dispatch. Both paths will fire for every `USER_MESSAGE` / `SUBAGENT_SEND`.
Queue Service dedups by `idempotency_key = msg:<id>`.

**Success criterion** — During the full observation window:

* Queue Service `action=deduped` rate equals subscriber dispatch rate
  (i.e. subscriber is NEVER the first to arrive; inline always wins the race).
* No ERROR / Traceback in `business-YYYYMMDD.log`.
* `message_outbox` row age stays < 30 s (no backlog).
* No `agent_owner_lookup ... result=miss` for canary agent.

---

## Deployment flow

### Phase 1 — Code rollout (`deploy-business.sh --first-time`)

From your dev machine:

```bash
# From the repo root
scripts/deploy-business.sh root@api.gradievo.com --first-time
```

This script:
1. Stops all backend services on the host.
2. Backs up `entangled.db` to `/opt/novaic/snapshots/entangled.db.bak-<ts>`.
3. Tarballs the current `/opt/novaic/services/` tree to `/opt/novaic/snapshots/services-<ts>.tar.gz`.
4. Rsyncs `novaic-business/`, `Entangled/`, `novaic-common/`, `scripts/`.
5. Starts services with the subscriber flag **OFF**.
6. Waits 60 s then verifies `message_outbox` schema exists.
7. Runs `/health` checks and tails the last ERROR lines for sanity.

**Expected result**: Subscriber is NOT enabled. System behaves exactly like
pre-deploy, except `message_outbox` is now being populated silently by every
message write (outbox is write-only at this stage, no consumer).

Let the system run like this for **≥ 30 min**. Watch:

```bash
ssh root@api.gradievo.com "tail -F /opt/novaic/data/logs/business-$(date +%Y%m%d).log \
    | grep -E 'ERROR|Traceback|caller=unknown|agent_owner_lookup.*miss'"
```

Expected: silent, no output.

Sanity check outbox is growing (there SHOULD be pending rows now since no consumer):

```bash
ssh root@api.gradievo.com \
    "sqlite3 /opt/novaic/data/entangled.db \
    'SELECT COUNT(*), MIN(created_at), MAX(created_at) FROM message_outbox'"
```

If count is 0 for a production system with real traffic, PR-14's
`ensure_schema` isn't wiring the outbox write correctly — **STOP, investigate
before Phase 2**.

### Phase 2 — Enable subscriber (Canary 阶段 1)

**TD-5 flow — edit `/opt/novaic/etc/runtime_switches.json` and restart.**
(PR-33 used to have you edit services.json directly; that was rsync-unsafe,
see §C.2.2. Never edit services.json on prod.)

On the production host:

```bash
ssh root@api.gradievo.com

# 1. Edit the runtime_switches overlay (single file, all services read it):
cat > /opt/novaic/etc/runtime_switches.json <<'JSON'
{
  "subscriber_enabled": true,
  "health_check_interval_seconds": 5,
  "scheduler_poll_interval_seconds": 1.0
}
JSON

# 2. Restart the stack:
bash /opt/novaic/start.sh --stop
bash /opt/novaic/start.sh
```

Verify in the startup snapshot — this line is the PR-33 audit target,
every service prints it exactly once per lifespan:

```bash
tail -200 /opt/novaic/data/logs/business-$(date +%Y%m%d).log | \
    grep -E 'runtime_switches=|dispatch_subscriber|worker_id'
```

Expected:
* `ServiceConfig: runtime_switches={"health_check_interval_seconds": 5, "scheduler_poll_interval_seconds": 1.0, "subscriber_enabled": true}`
* `dispatch_subscriber enabled worker_id=<host>:<pid>:<uuid8>`

If the `runtime_switches` line shows `subscriber_enabled: false`, the
overlay at `/opt/novaic/etc/runtime_switches.json` is either missing,
empty, or failed to load. Check:
* `cat /opt/novaic/etc/runtime_switches.json` — file present + valid JSON?
* `grep 'runtime_switches overlay applied' /opt/novaic/data/logs/business-$(date +%Y%m%d).log` — loader INFO line lists your keys?
* Startup error line matching `unknown key(s)` — overlay has a typo'd key;
  fix and restart.

**Start the observation clock (T0).** Watch for **4 hours** continuously.

#### What to watch

1. **Business log** — `tail -F` on business + entangled + queue logs:

    ```bash
    tail -F /opt/novaic/data/logs/business-$(date +%Y%m%d).log \
            /opt/novaic/data/logs/entangled.log \
            /opt/novaic/data/logs/queue.log \
        | grep -E 'ERROR|Traceback|subscriber_tick|event=dispatch|action=deduped|health_fallback'
    ```

2. **Outbox health** — every 15 min:

    ```bash
    python3 /opt/novaic/services/scripts/canary/traffic.py observe
    ```

    Expected: `oldest_pending_age < 30s`, `poisoned == 0`, `retrying` stable near 0.

3. **Dedup rate sanity** — the first message the subscriber delivers SHOULD be
   a duplicate (Queue Service returns `action=deduped`). Rough formula:

    ```bash
    # number of subscriber deliveries
    grep -c 'subscriber_tick delivered' /opt/novaic/data/logs/business-*.log
    # number of deduped hits from Queue
    grep -c 'action=deduped' /opt/novaic/data/logs/queue-*.log
    ```

    These should be within ~5% of each other. If `deduped` count is
    dramatically lower, that means inline dispatch is losing the race to the
    subscriber, or the idempotency ledger is broken. Stop and investigate.

4. **Canary self-test** — once an hour, fire a 10-message burst and confirm
   observe() reports `oldest_pending_age < 5s`:

    ```bash
    python3 /opt/novaic/services/scripts/canary/traffic.py bootstrap     # first time only
    python3 /opt/novaic/services/scripts/canary/traffic.py send --count 10 --tps 2
    sleep 10
    python3 /opt/novaic/services/scripts/canary/traffic.py observe
    ```

#### Abort criteria (ANY of these → immediate Phase 4 rollback)

* 1+ ERROR / Traceback in `business-*.log` referencing subscriber / outbox / assembler.
* `oldest_pending_age_sec > 60` sustained for 2 minutes.
* `poisoned > 0` rows in outbox (any single permanent failure warrants investigation).
* Queue Service dedup rate < 80% of subscriber deliveries.
* `agent_owner_lookup ... result=miss` rate noticeably elevated (indicates
  PR-08 resolver regression).

### Phase 3 — Load test (operator-assisted, at a planned time window)

The user (operator) MUST be present at a keyboard during this phase.

```bash
ssh root@api.gradievo.com
# Ensure canary agent exists (idempotent)
python3 /opt/novaic/services/scripts/canary/traffic.py bootstrap

# Warm-up
python3 /opt/novaic/services/scripts/canary/traffic.py send --count 20 --tps 5
python3 /opt/novaic/services/scripts/canary/traffic.py observe

# Real load test (100 msg over 10 s)
python3 /opt/novaic/services/scripts/canary/traffic.py send --count 100 --tps 10 --concurrency 5
sleep 15
python3 /opt/novaic/services/scripts/canary/traffic.py observe
```

Expected:
* All 100 sends return 2xx.
* Within 15 s: `oldest_pending_age_sec < 5`, `pending == 0` (or small transient).
* Queue Service receives exactly 100 × 2 = 200 dispatches; 100 of them are deduped.

If any of the above fails → Phase 4 rollback.

### Phase 4 — Extended natural-traffic observation

After a successful Phase 3, let the system run another **4–6 hours** under
natural traffic with subscriber ON. During this time, continuously tail logs
and run `observe` every 30 min.

### Phase 5 — Canary success

If Phase 1–4 all succeed:

1. Commit a decision note in `docs/roadmap/tickets/PR-17-canary-enable-subscriber.md`
   with start/end timestamps, sample outbox stats, dedup ratios.
2. Keep `subscriber_enabled: true` in the production overlay
   `/opt/novaic/etc/runtime_switches.json` going forward. (PR-33 landed
   2026-04-20, TD-5 overlay 2026-04-15; the env var
   `NOVAIC_ENABLE_SUBSCRIBER` is dead — do not re-introduce it. Editing
   `services.json` on prod is also dead — overlay wins, next rsync stomps
   your edit.)
3. Do NOT yet remove the inline `_dispatch_trigger` shim (that's PR-18).

---

## Rollback playbook

### Fast rollback — subscriber only (preserve data, < 45 s)

**TD-5 flow**: flip `subscriber_enabled` back to `false` in the overlay
and restart. There is no env var to unset and no services.json edit to
revert.

```bash
ssh root@api.gradievo.com

cat > /opt/novaic/etc/runtime_switches.json <<'JSON'
{
  "subscriber_enabled": false,
  "health_check_interval_seconds": 30,
  "scheduler_poll_interval_seconds": 1.0
}
JSON

bash /opt/novaic/start.sh --stop
bash /opt/novaic/start.sh
```

Verification SLO: from the moment `--stop` returns to the moment
`business-*.log` prints `dispatch_subscriber disabled
(runtime_switches.subscriber_enabled=false)`, elapsed time MUST be ≤ 45 s.
If not, that is itself a bug — escalate. Also confirm the
`runtime_switches=` snapshot line for this restart shows
`subscriber_enabled: false`; if it still says `true`, the edit did not
land (wrong file, or an error earlier in startup aborted before
config reload).

**Side effect to be aware of**: `message_outbox` will keep accumulating rows
(Entangled co-transactionally writes them on every message), but with no
consumer they'll stay pending. This is fine for a few days, but if the
subscriber stays off for > 7 days, run `scripts/outbox-compact.sh` manually
or accept the disk-space growth.

### Full code rollback (nuclear option)

If the Phase 1 deployment itself is suspect (Entangled schema broken, code
regression unrelated to subscriber):

```bash
ssh root@api.gradievo.com
bash /opt/novaic/start.sh --stop
cd /opt/novaic
tar xzf snapshots/services-<TIMESTAMP>.tar.gz
cp snapshots/entangled.db.bak-<TIMESTAMP> data/entangled.db
bash /opt/novaic/start.sh
```

Verify all `/health` endpoints are 200.

---

## Monitoring without Prometheus (PR-32 backlog)

PR-16 deferred Prometheus metrics to PR-32. Until then, use these shell-based
substitutes:

| Metric (future)              | Shell equivalent                                                                                                                     |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| `subscriber_delivered_total` | `grep -c 'subscriber_tick delivered' business-*.log`                                                                                  |
| `subscriber_failed_total`    | `grep -cE 'subscriber_tick .*failed=[1-9]' business-*.log`                                                                            |
| `outbox_lag_seconds`         | `python3 scripts/canary/traffic.py observe` → `oldest_pending_age_sec`                                                                |
| `outbox_claim_batch_size`    | `grep -oE 'claimed=[0-9]+' business-*.log \| sort \| uniq -c`                                                                           |
| `dispatch_dedup_rate`        | Queue log: `grep -c action=deduped queue-*.log` ÷ `grep -c 'subscriber_tick delivered' business-*.log`                                |

---

## Troubleshooting cheat-sheet

| Symptom                                              | Likely cause                                                      | Action                                                                                     |
| ---------------------------------------------------- | ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| `message_outbox` missing after first-time deploy     | Entangled not restarted / PR-14 code missing                      | Verify PR-14 commit present on host; restart Entangled.                                    |
| `poisoned > 0` in outbox                             | Agent has no owner, or Queue Service rejected payload as bad 400  | Read `business-*.log` for the matching `subscriber_tick` error; investigate specific row.  |
| Subscriber delivers FIRST, inline deduped second     | Inline dispatch is broken (stuck `await`, network error, etc.)    | Confirm via `grep 'event=dispatch .*result=ok' business-*.log` — if rare, inline is down.  |
| `oldest_pending_age` keeps growing                   | Subscriber crashed / not running                                  | Check `grep 'dispatch_subscriber' business-*.log \| tail`. Restart with flag ON if needed.  |
| `health_fallback` rate spike                         | Inline dispatch is silently failing; fallback is catching         | Inspect `event=dispatch .*result=` distribution; rollback subscriber first, then debug.    |
| Rollback elapsed time > 45 s                         | overlay's `health_check_interval_seconds` still 30 | Confirm `/opt/novaic/etc/runtime_switches.json` holds your edited value AND the `runtime_switches=` startup snapshot reflects it; overlay miss ⇒ file missing / bad JSON / typo'd key (ConfigError in startup log). |

---

## Appendix A — Production paths reference

| Path                                                          | What                                |
| ------------------------------------------------------------- | ----------------------------------- |
| `/opt/novaic/services/novaic-business/`                       | Business service code               |
| `/opt/novaic/services/Entangled/`                             | Entangled storage layer             |
| `/opt/novaic/services/novaic-common/`                         | Shared library                      |
| `/opt/novaic/start.sh`                       | Backend startup script (all services) |
| `/opt/novaic/services/scripts/canary/traffic.py`              | This runbook's traffic tool         |
| `/opt/novaic/data/entangled.db`                               | SQLite file with `message_outbox`   |
| `/opt/novaic/data/logs/business-YYYYMMDD.log`                 | Business log (daily rotated)        |
| `/opt/novaic/data/logs/health.log`                            | HealthWorker log                    |
| `/opt/novaic/data/logs/queue.log`                             | Queue Service log (dedup hits here) |
| `/opt/novaic/snapshots/entangled.db.bak-<ts>`                 | Pre-deploy DB backups               |
| `/opt/novaic/snapshots/services-<ts>.tar.gz`                  | Pre-deploy code snapshots           |

## Appendix B — Canary identity

| Field                   | Value                                                     |
| ----------------------- | --------------------------------------------------------- |
| Canary user id          | `canary_u_1` (permanent, no gateway/auth side row needed) |
| Canary agent id         | `canary_a_1`                                              |
| Agent name              | `Canary Observation Agent`                                |
| Created via             | `scripts/canary/traffic.py bootstrap`                     |
| Expected ownership path | `GET /internal/agents/canary_a_1/owner` → `canary_u_1`    |

Never delete these. They're used on every Canary and production smoke test.
