#!/usr/bin/env bash
# PR-17 Phase 4 bake snapshot (run via cron, 4h cadence)
#
# Usage:
#   scripts/canary/bake-snapshot.sh >> /opt/novaic/data/logs/pr17-bake.log 2>&1
#
# Install (crontab -e as root):
#   0 */4 * * * /opt/novaic/services/scripts/canary/bake-snapshot.sh >> /opt/novaic/data/logs/pr17-bake.log 2>&1
#
# Output: one block per run, pipe-friendly so the whole file stays
# tail-and-rg-able. Intentionally uses no color, no emojis.

set -uo pipefail

PY="${PY:-/opt/novaic/services/novaic-gateway/.venv/bin/python}"
TRAFFIC="/opt/novaic/services/scripts/canary/traffic.py"
LOGDIR="/opt/novaic/data/logs"
TODAY="$(date -u +%Y%m%d)"
BLOG="$LOGDIR/business-$TODAY.log"
HLOG="$LOGDIR/health.log"                  # rotating current
HLOG_DATED="$LOGDIR/health-$TODAY.log"     # daily archive (legacy)

ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "=== PR17-BAKE $ts ==="

# 1. outbox snapshot (uses traffic.py::observe)
if [ -x "$PY" ] && [ -f "$TRAFFIC" ]; then
    "$PY" "$TRAFFIC" observe | sed 's/^/  outbox   /' || true
else
    echo "  outbox   skip: $PY or $TRAFFIC missing"
fi

# 2. business log counters (PR-17 Canary judges)
#
# Business service names its log file at startup using the UTC start date
# (e.g. business-20260418.log) and does NOT rotate daily. Once the process
# crosses UTC midnight, today-dated file will not exist; we fall back to the
# most recent business-*.log so the counters remain observable. This also
# future-proofs the script in case daily rotation is added later (today-
# dated file, when present, always wins).
BSRC=""
if [ -f "$BLOG" ]; then
    BSRC="$BLOG"
else
    BSRC="$(ls -1t "$LOGDIR"/business-*.log 2>/dev/null | head -n 1)"
fi
if [ -n "$BSRC" ] && [ -f "$BSRC" ]; then
    label="$BSRC"
    [ "$BSRC" != "$BLOG" ] && label="$BSRC (fallback: $(basename "$BLOG") not present)"
    echo "  biz_log  file=$label size=$(stat -c%s "$BSRC")"
    for pat in \
        "event=subscriber_delivered:delivered" \
        "subscriber permanent fail:perm_fail" \
        "subscriber transient:transient" \
        "action=deduped:deduped" \
        "action=saga_started:saga_started" \
        "action=buffered:buffered" ; do
        k="${pat##*:}"
        p="${pat%:*}"
        n="$(grep -c -- "$p" "$BSRC" 2>/dev/null | head -n 1)"
        : "${n:=0}"
        printf "  biz_log  %-18s = %s\n" "$k" "$n"
    done
else
    echo "  biz_log  skip: no business-*.log in $LOGDIR"
fi

# 3. health worker log counters (PR-19 will fix 401; tracked here as baseline)
HSOURCE="$HLOG"; [ -f "$HLOG" ] || HSOURCE="$HLOG_DATED"
if [ -f "$HSOURCE" ]; then
    echo "  hlth_log file=$HSOURCE size=$(stat -c%s "$HSOURCE")"
    for pat in \
        "Recovery API returned 401:recover_401" \
        "event=health_fallback.*result=ok:fallback_ok" \
        "Skip waking.*queue_400:skip_queue_400" \
        "Fallback dispatch failed:legacy_400" \
        "event=health_fallback_capped:capped" ; do
        k="${pat##*:}"
        p="${pat%:*}"
        n="$(grep -cE -- "$p" "$HSOURCE" 2>/dev/null | head -n 1)"
        : "${n:=0}"
        printf "  hlth_log %-18s = %s\n" "$k" "$n"
    done
else
    echo "  hlth_log skip: neither $HLOG nor $HLOG_DATED"
fi

# 4. Phase 1 red lines (from docs/roadmap/tickets/reviews/PR-17-preflight-guidance.md §C phase 1)
#    Re-query the SQLite directly as a sanity cross-check vs traffic.py
DB="/opt/novaic/data/entangled.db"
if [ -r "$DB" ]; then
    pend_cnt="$(sqlite3 "$DB" 'SELECT COUNT(*) FROM message_outbox WHERE delivered_at IS NULL;')"
    pois_cnt="$(sqlite3 "$DB" 'SELECT COUNT(*) FROM message_outbox WHERE delivered_at IS NULL AND attempts >= 999999;')"
    oldest="$(sqlite3 "$DB" 'SELECT COALESCE(MAX((strftime("%s","now")*1000 - created_at)/1000),0) FROM message_outbox WHERE delivered_at IS NULL;')"
    verdict="OK"
    [ "$pend_cnt" -gt 50 ]  && verdict="WARN(pending>$pend_cnt)"
    [ "$pois_cnt" -gt 0 ]   && verdict="WARN(poisoned=$pois_cnt)"
    [ "$oldest"   -gt 300 ] && verdict="WARN(age=${oldest}s)"
    printf "  redline  pending=%s poisoned=%s oldest_age_s=%s verdict=%s\n" \
        "$pend_cnt" "$pois_cnt" "$oldest" "$verdict"
else
    echo "  redline  skip: $DB not readable"
fi

echo
