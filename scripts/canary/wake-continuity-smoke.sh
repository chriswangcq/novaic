#!/usr/bin/env bash
#
# PR-45.2 / P6-13 FOLLOW-UP — wake-continuity smoke test (R9 text layer).
#
# Purpose
# -------
# Post-deploy / nightly probe that R9 text-layer wake continuity is
# actually firing on prod (not just unit-test green). The chain being
# probed end-to-end:
#
#     traffic.send USER_MESSAGE
#   → message_actions writes chat_messages + outbox
#   → DispatchSubscriber claims outbox row
#   → _resolve_continuity reads subagents.{handoff_notes, historical_summary}
#   → emits `event=continuity_resolve result=ok|empty|not_found` (PR-45.1)
#   → merges into payload.metadata
#   → Assembler → queue → runtime session.init
#   → _build_wake_continuity_messages renders <HANDOFF_NOTES> / <HISTORICAL_SUMMARY>
#
# A canary PASS means: (a) a fresh USER_MESSAGE was accepted, (b) the
# subscriber ran _resolve_continuity for the canary agent within the
# observation window, (c) no `result=error` lines appeared, (d) the
# subagents row is readable (not 500/timeout). The canary does NOT
# require handoff_notes to be populated — a brand-new canary agent
# will legitimately resolve to `result=not_found` or `result=empty`
# on first hit, and that's a valid positive signal that the path
# executed (the regression shape this probe catches is "resolver
# never ran" — silent zero signal — not "resolver returned empty").
#
# Why this exists
# ---------------
# PR-45 review §3.3 called out that during Wave 1F review (2026-04-24)
# there was no direct live evidence of the producer path firing,
# only state-machine + unit-test coverage. PR-45.1 added the
# `logger.info(event=continuity_resolve ...)` line that makes the
# resolve observable; this script *uses* that log line as a passing
# signal. Before PR-45.1 this probe wouldn't have been possible
# without SQL inspection of the subagents row (indirect).
#
# Usage
# -----
#   # From a box with loopback access to Business (127.0.0.1:19998):
#   ./scripts/canary/wake-continuity-smoke.sh
#
#   # Override the log path (on prod the subscriber log is typically
#   # under /var/log/novaic/business.log or journalctl):
#   LOG_PATH=/var/log/novaic/business.log \
#     ./scripts/canary/wake-continuity-smoke.sh
#
#   # Use journalctl as the log source:
#   LOG_SOURCE=journalctl ./scripts/canary/wake-continuity-smoke.sh
#
# Environment
# -----------
#   BUSINESS_URL         default http://127.0.0.1:19998
#   CANARY_AGENT_ID      default canary_b_1 (separate from PR-17's canary_a_1)
#   CANARY_USER_ID       default canary_bu_1
#   CANARY_AGENT_NAME    default "Canary Wake-Continuity Agent"
#   LOG_SOURCE           default "file" (alt: "journalctl")
#   LOG_PATH             when LOG_SOURCE=file, default ./business.log
#                        (looked up in several common locations)
#   LOG_UNIT             when LOG_SOURCE=journalctl, default novaic-business
#   WAIT_SECONDS         default 45 — how long to wait for resolve log
#
# Exit codes
# ----------
#   0  — PASS (resolve observed, no errors)
#   1  — FAIL (log path missing / no resolve seen / resolver errored)
#   2  — FAIL (prerequisite missing — bootstrap or send failed)
#   3  — SKIP (log source unreadable — env not configured correctly)
#
# Wiring
# ------
# This probe is meant to be called from a nightly cron / bake snapshot
# loop. On FAIL, page whoever owns the wake-continuity path. Current
# owner is documented in docs/architecture/message-wake-principles.md
# §R9.
set -eo pipefail

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
TRAFFIC_PY="$SCRIPT_DIR/traffic.py"

# ── Config ─────────────────────────────────────────────────────────────
export CANARY_BUSINESS_URL="${BUSINESS_URL:-http://127.0.0.1:19998}"
export CANARY_AGENT_ID="${CANARY_AGENT_ID:-canary_b_1}"
export CANARY_USER_ID="${CANARY_USER_ID:-canary_bu_1}"
export CANARY_AGENT_NAME="${CANARY_AGENT_NAME:-Canary Wake-Continuity Agent}"

LOG_SOURCE="${LOG_SOURCE:-file}"
LOG_UNIT="${LOG_UNIT:-novaic-business}"
WAIT_SECONDS="${WAIT_SECONDS:-45}"

# Default candidate log paths (first readable wins). Most prod boxes
# run Business either under a systemd unit (journalctl) or with stdout
# redirected to one of these paths.
CANDIDATE_LOG_PATHS=(
    "${LOG_PATH:-}"
    "/var/log/novaic/business.log"
    "/opt/novaic/logs/business.log"
    "$PWD/business.log"
    "$PWD/logs/business.log"
)

# ── Helpers ────────────────────────────────────────────────────────────

_ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }

_log() { echo "[$(_ts)] $*"; }

_pick_log_path() {
    for p in "${CANDIDATE_LOG_PATHS[@]}"; do
        [[ -z "$p" ]] && continue
        if [[ -r "$p" ]]; then
            echo "$p"
            return 0
        fi
    done
    return 1
}

# ── Phase 0: Resolve log source ────────────────────────────────────────

if [[ "$LOG_SOURCE" == "file" ]]; then
    if ! LOG_FILE=$(_pick_log_path); then
        _log "SKIP: no readable log path (tried: ${CANDIDATE_LOG_PATHS[*]})"
        _log "      Set LOG_PATH=/abs/path or LOG_SOURCE=journalctl"
        exit 3
    fi
    _log "using log file: $LOG_FILE"
elif [[ "$LOG_SOURCE" == "journalctl" ]]; then
    if ! command -v journalctl >/dev/null 2>&1; then
        _log "SKIP: journalctl not available (LOG_SOURCE=journalctl requires systemd)"
        exit 3
    fi
    _log "using journalctl unit: $LOG_UNIT"
else
    _log "SKIP: unsupported LOG_SOURCE=$LOG_SOURCE (expected file|journalctl)"
    exit 3
fi

# ── Phase 1: Bootstrap canary agent ────────────────────────────────────

_log "phase 1/4: bootstrap canary agent=$CANARY_AGENT_ID user=$CANARY_USER_ID"
if ! python3 "$TRAFFIC_PY" bootstrap; then
    _log "FAIL: bootstrap failed — check Business URL ($CANARY_BUSINESS_URL) and"
    _log "      /internal/entities/agents endpoint availability."
    exit 2
fi

# ── Phase 2: Record log cursor ─────────────────────────────────────────
#
# Capture the current log position so we only look at lines produced
# AFTER our send — avoids false positives from earlier traffic.

SINCE_TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

if [[ "$LOG_SOURCE" == "file" ]]; then
    # Use byte offset as the cursor; new content starts at offset `LOG_CURSOR`.
    LOG_CURSOR=$(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE" 2>/dev/null || echo 0)
    _log "phase 2/4: log cursor at byte $LOG_CURSOR"
else
    _log "phase 2/4: journalctl cursor at $SINCE_TS"
fi

# ── Phase 3: Send 1 USER_MESSAGE ───────────────────────────────────────

_log "phase 3/4: send 1 USER_MESSAGE"
if ! python3 "$TRAFFIC_PY" send --count 1 --tps 1 --concurrency 1; then
    _log "FAIL: send failed — check message_actions.send_action reachability"
    exit 2
fi

# ── Phase 4: Wait for continuity resolve log ───────────────────────────

_log "phase 4/4: wait up to ${WAIT_SECONDS}s for event=continuity_resolve"

# Pattern we're looking for in the business subscriber log. PR-45.1
# emits this line with per-dispatch granularity; a single hit matching
# our canary agent proves the resolver path executed.
GREP_PAT="event=continuity_resolve.*agent=${CANARY_AGENT_ID}"

deadline=$(( $(date +%s) + WAIT_SECONDS ))
found_ok=0
found_empty=0
found_not_found=0
found_error=0
matched_lines=""

while [[ $(date +%s) -lt $deadline ]]; do
    if [[ "$LOG_SOURCE" == "file" ]]; then
        # Read only bytes after the cursor.
        tail -c "+$((LOG_CURSOR + 1))" "$LOG_FILE" 2>/dev/null > /tmp/.wc_tail.$$ || true
        lines=$(grep -E "$GREP_PAT" /tmp/.wc_tail.$$ 2>/dev/null || true)
        rm -f /tmp/.wc_tail.$$
    else
        lines=$(journalctl -u "$LOG_UNIT" --since "$SINCE_TS" --no-pager 2>/dev/null |
                grep -E "$GREP_PAT" || true)
    fi

    if [[ -n "$lines" ]]; then
        matched_lines="$lines"
        # Classify outcomes.
        found_ok=$(echo "$lines" | grep -c "result=ok" || true)
        found_empty=$(echo "$lines" | grep -c "result=empty" || true)
        found_not_found=$(echo "$lines" | grep -c "result=not_found" || true)
        found_error=$(echo "$lines" | grep -c "result=error" || true)
        break
    fi
    sleep 2
done

# ── Verdict ────────────────────────────────────────────────────────────

if [[ -z "$matched_lines" ]]; then
    _log "FAIL: no event=continuity_resolve line seen within ${WAIT_SECONDS}s"
    _log "      → either DispatchSubscriber is not running, _resolve_continuity"
    _log "        is not being called, or the message never claimed through outbox."
    _log "      → check: ps aux | grep dispatch_subscriber"
    _log "      → check: python3 $TRAFFIC_PY observe (outbox backlog?)"
    exit 1
fi

_log "observed continuity resolve lines:"
echo "$matched_lines" | sed 's/^/    /'
_log "outcomes: ok=$found_ok empty=$found_empty not_found=$found_not_found error=$found_error"

if [[ $found_error -gt 0 ]]; then
    _log "FAIL: _resolve_continuity hit an error branch (Business unreachable"
    _log "      or subagents endpoint 500). Investigate before trusting"
    _log "      continuity on downstream dispatches."
    exit 1
fi

# PASS — the resolve fired. A brand-new canary will usually see
# result=not_found on first-hit (subagent row materialized by
# runtime on session.init AFTER this message, not before); a
# subsequent run will see result=empty (row exists, fields NULL).
# Neither is a failure — they both prove the producer path is
# wired. The failure shape is "resolver never ran at all", which
# the empty-match branch above catches.
_log "PASS: wake-continuity resolver executed for agent=$CANARY_AGENT_ID"
_log "      (result=ok is not required; empty / not_found are also"
_log "       valid positive signals — see script header for why.)"
exit 0
