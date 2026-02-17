#!/usr/bin/env bash
set -euo pipefail

# End-to-end health gate:
# - strict isolated stack startup (RO/Queue/TRS/Gateway/Tools/Workers)
# - load test (default: 3 msg/s * 30s)
# - hard assertions for agent loop and TRS/runtime_rest path
#
# Usage:
#   bash scripts/health_gate_agent_loop.sh
#   DURATION_SECONDS=30 RATE_PER_SECOND=3 bash scripts/health_gate_agent_loop.sh

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

if [[ -x "${ROOT_DIR}/venv/bin/python" ]]; then
  PYTHON_CMD="${ROOT_DIR}/venv/bin/python"
elif [[ -x "${ROOT_DIR}/.venv/bin/python" ]]; then
  PYTHON_CMD="${ROOT_DIR}/.venv/bin/python"
else
  PYTHON_CMD="python3"
fi

export NO_PROXY="localhost,127.0.0.1,::1"
export no_proxy="localhost,127.0.0.1,::1"
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY || true

RATE_PER_SECOND="${RATE_PER_SECOND:-3}"
DURATION_SECONDS="${DURATION_SECONDS:-30}"
DRAIN_SECONDS="${DRAIN_SECONDS:-20}"

RO_PORT="${RO_PORT:-29993}"
QUEUE_PORT="${QUEUE_PORT:-29997}"
TRS_PORT="${TRS_PORT:-29994}"
TOOLS_PORT="${TOOLS_PORT:-29998}"
GW_PORT="${GW_PORT:-29999}"

RO_URL="http://127.0.0.1:${RO_PORT}"
QUEUE_URL="http://127.0.0.1:${QUEUE_PORT}"
TRS_URL="http://127.0.0.1:${TRS_PORT}"
TOOLS_URL="http://127.0.0.1:${TOOLS_PORT}"
GW_URL="http://127.0.0.1:${GW_PORT}"

STAMP="$(${PYTHON_CMD} - <<'PY'
import time
print(time.strftime('%Y%m%d-%H%M%S'))
PY
)"
DATA_DIR="${DATA_DIR:-/tmp/novaic-health-gate-${STAMP}}"
LOG_DIR="${DATA_DIR}/logs"
mkdir -p "${LOG_DIR}"

echo "[health-gate] DATA_DIR=${DATA_DIR}"
echo "[health-gate] Python=${PYTHON_CMD}"

declare -a PIDS=()
cleanup() {
  set +e
  for pid in "${PIDS[@]:-}"; do
    if [[ -n "${pid}" ]] && kill -0 "${pid}" 2>/dev/null; then
      kill "${pid}" 2>/dev/null || true
    fi
  done
  sleep 0.5
  for pid in "${PIDS[@]:-}"; do
    if [[ -n "${pid}" ]] && kill -0 "${pid}" 2>/dev/null; then
      kill -9 "${pid}" 2>/dev/null || true
    fi
  done
  for pid in "${PIDS[@]:-}"; do
    if [[ -n "${pid}" ]]; then
      wait "${pid}" 2>/dev/null || true
    fi
  done
}
trap cleanup EXIT

# hard clear stale processes
pkill -f "main_novaic.py runtime-orchestrator|main_novaic.py queue-service|main_novaic.py tool-result-service|main_novaic.py tools-server|main_novaic.py gateway|main_novaic.py watchdog|main_novaic.py task-worker|main_novaic.py saga-worker|task_worker_sync|saga_worker_sync|watchdog_sync|health_worker_sync" >/dev/null 2>&1 || true

start_proc() {
  local name="$1"
  local cmd="$2"
  local log_file="$3"
  echo "[health-gate] starting ${name}"
  bash -lc "${cmd}" >"${log_file}" 2>&1 &
  local pid=$!
  PIDS+=("${pid}")
  echo "[health-gate] ${name} pid=${pid}"
}

wait_http() {
  local name="$1"
  local url="$2"
  local max_tries="${3:-80}"
  for _ in $(seq 1 "${max_tries}"); do
    if curl -sS "${url}" >/dev/null 2>&1; then
      echo "[health-gate] ${name} healthy (${url})"
      return 0
    fi
    sleep 0.25
  done
  echo "[health-gate] ERROR: ${name} health timeout (${url})"
  return 1
}

start_proc "runtime-orchestrator" \
  "NO_PROXY=localhost,127.0.0.1 no_proxy=localhost,127.0.0.1 ${PYTHON_CMD} main_novaic.py runtime-orchestrator --host 127.0.0.1 --port ${RO_PORT} --data-dir '${DATA_DIR}'" \
  "${LOG_DIR}/ro.log"
start_proc "queue-service" \
  "NO_PROXY=localhost,127.0.0.1 no_proxy=localhost,127.0.0.1 ${PYTHON_CMD} main_novaic.py queue-service --host 127.0.0.1 --port ${QUEUE_PORT} --data-dir '${DATA_DIR}'" \
  "${LOG_DIR}/queue.log"
start_proc "tool-result-service" \
  "NO_PROXY=localhost,127.0.0.1 no_proxy=localhost,127.0.0.1 ${PYTHON_CMD} main_novaic.py tool-result-service --host 127.0.0.1 --port ${TRS_PORT} --data-dir '${DATA_DIR}'" \
  "${LOG_DIR}/trs.log"

wait_http "runtime-orchestrator" "${RO_URL}/api/health"
wait_http "queue-service" "${QUEUE_URL}/health"
wait_http "tool-result-service" "${TRS_URL}/api/health"

start_proc "gateway" \
  "NO_PROXY=localhost,127.0.0.1 no_proxy=localhost,127.0.0.1 ${PYTHON_CMD} main_novaic.py gateway --host 127.0.0.1 --port ${GW_PORT} --data-dir '${DATA_DIR}' --runtime-orchestrator-url ${RO_URL} --queue-service-url ${QUEUE_URL} --tools-server-url ${TOOLS_URL} --vmcontrol-url http://127.0.0.1:29996 --file-service-url http://127.0.0.1:29995 --tool-result-service-url ${TRS_URL}" \
  "${LOG_DIR}/gateway.log"
wait_http "gateway" "${GW_URL}/api/health"

start_proc "tools-server" \
  "NO_PROXY=localhost,127.0.0.1 no_proxy=localhost,127.0.0.1 ${PYTHON_CMD} main_novaic.py tools-server --host 127.0.0.1 --port ${TOOLS_PORT} --data-dir '${DATA_DIR}' --gateway-url ${GW_URL} --runtime-orchestrator-url ${RO_URL} --tool-result-service-url ${TRS_URL}" \
  "${LOG_DIR}/tools.log"
wait_http "tools-server" "${TOOLS_URL}/api/health"

start_proc "watchdog" \
  "NO_PROXY=localhost,127.0.0.1 no_proxy=localhost,127.0.0.1 ${PYTHON_CMD} main_novaic.py watchdog --gateway-url ${GW_URL} --queue-service-url ${QUEUE_URL} --runtime-orchestrator-url ${RO_URL} --data-dir '${DATA_DIR}'" \
  "${LOG_DIR}/watchdog.log"
start_proc "task-worker" \
  "NO_PROXY=localhost,127.0.0.1 no_proxy=localhost,127.0.0.1 ${PYTHON_CMD} main_novaic.py task-worker --gateway-url ${GW_URL} --queue-service-url ${QUEUE_URL} --tools-server-url ${TOOLS_URL} --runtime-orchestrator-url ${RO_URL} --tool-result-service-url ${TRS_URL} --num-workers 2 --data-dir '${DATA_DIR}'" \
  "${LOG_DIR}/task-worker.log"
start_proc "saga-worker" \
  "NO_PROXY=localhost,127.0.0.1 no_proxy=localhost,127.0.0.1 ${PYTHON_CMD} main_novaic.py saga-worker --gateway-url ${GW_URL} --queue-service-url ${QUEUE_URL} --runtime-orchestrator-url ${RO_URL} --max-concurrent 10 --data-dir '${DATA_DIR}'" \
  "${LOG_DIR}/saga-worker.log"

REPORT_STDOUT_FILE="${DATA_DIR}/health_gate_stdout.txt"
set +e
${PYTHON_CMD} - <<PY > "${REPORT_STDOUT_FILE}"
import json,time,urllib.request,sqlite3,collections,re,sys,pathlib

GW_URL = "${GW_URL}"
DATA_DIR = "${DATA_DIR}"
RATE_PER_SECOND = int("${RATE_PER_SECOND}")
DURATION_SECONDS = int("${DURATION_SECONDS}")
DRAIN_SECONDS = int("${DRAIN_SECONDS}")

def req_json(url, method="GET", payload=None, timeout=8):
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read().decode()
        return r.getcode(), (json.loads(body) if body else {})

# ensure one agent exists
_, agents = req_json(GW_URL + "/api/agents")
arr = agents.get("agents", [])
if arr:
    agent_id = arr[0]["id"]
else:
    _, created = req_json(GW_URL + "/api/agents", method="POST", payload={"name": "Health Gate Agent"})
    agent_id = created.get("id") or ((created.get("agents") or [{}])[0].get("id"))

start_ts = time.time()
start_iso = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(start_ts))

send_errors = []
message_ids = []
lat_ms = []
for sec in range(DURATION_SECONDS):
    slot = time.time()
    for i in range(RATE_PER_SECOND):
        text = f"health gate ping s{sec:02d} i{i} t{int(time.time()*1000)}"
        t0 = time.time()
        try:
            _, msg = req_json(
                GW_URL + "/internal/messages",
                method="POST",
                payload={"agent_id": agent_id, "type": "USER_MESSAGE", "content": text},
                timeout=6,
            )
            message_ids.append(msg.get("id"))
            lat_ms.append((time.time() - t0) * 1000.0)
        except Exception as e:
            send_errors.append(str(e))
    dt = time.time() - slot
    if dt < 1.0:
        time.sleep(1.0 - dt)

for _ in range(DRAIN_SECONDS):
    time.sleep(1)

status_counts = collections.Counter()
for mid in message_ids:
    if not mid:
        status_counts["missing_id"] += 1
        continue
    try:
        _, m = req_json(GW_URL + f"/internal/messages/{mid}", timeout=4)
        status_counts[m.get("status", "unknown")] += 1
    except Exception:
        status_counts["query_error"] += 1

conn = sqlite3.connect(f"{DATA_DIR}/gateway.db")
conn.row_factory = sqlite3.Row
c = conn.cursor()
c.execute("select type,status,count(*) c from chat_messages where agent_id=? and timestamp>=? group by type,status", (agent_id, start_iso))
chat_breakdown = [dict(r) for r in c.fetchall()]
conn.close()

conn = sqlite3.connect(f"{DATA_DIR}/queue.db")
conn.row_factory = sqlite3.Row
c = conn.cursor()
c.execute("select topic,status,count(*) c from tq_tasks where created_at>=? group by topic,status order by topic,status", (start_iso,))
task_breakdown = [dict(r) for r in c.fetchall()]
c.execute("select saga_type,status,count(*) c from tq_sagas where created_at>=? group by saga_type,status order by saga_type,status", (start_iso,))
saga_breakdown = [dict(r) for r in c.fetchall()]
c.execute("select payload,result from tq_tasks where topic='tool.execute' and created_at>=?", (start_iso,))
tool_per_name = collections.defaultdict(lambda: {"count": 0, "success_true": 0, "success_false": 0, "sample_error": None})
for r in c.fetchall():
    try:
        payload = json.loads(r["payload"] or "{}")
    except Exception:
        payload = {}
    try:
        result = json.loads(r["result"] or "{}")
    except Exception:
        result = {}
    name = payload.get("tool_name", "<unknown>")
    succ = result.get("success")
    d = tool_per_name[name]
    d["count"] += 1
    if succ is True:
        d["success_true"] += 1
    elif succ is False:
        d["success_false"] += 1
        if not d["sample_error"]:
            d["sample_error"] = result.get("error")
conn.close()

ro_conn = sqlite3.connect(f"{DATA_DIR}/runtime_orchestrator.db")
ro_c = ro_conn.cursor()
ro_c.execute("select count(*) from agent_runtimes")
runtime_count = ro_c.fetchone()[0]
ro_conn.close()

log_dir = pathlib.Path(DATA_DIR) / "logs"
log_text = ""
for p in log_dir.glob("*.log"):
    try:
        log_text += p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        pass

forbidden_patterns = {
    "trs_connection_refused": r"Failed to store result in TRS|to_llm_content failed.*Connection refused|get_preview failed.*Connection refused",
    "ro_internal_messages_404": r"POST http://127\.0\.0\.1:\d+/internal/messages .*404",
}
forbidden_hits = {}
for key, pat in forbidden_patterns.items():
    m = re.findall(pat, log_text)
    forbidden_hits[key] = len(m)

expected_total = RATE_PER_SECOND * DURATION_SECONDS
chat_counts = {(x["type"], x["status"]): x["c"] for x in chat_breakdown}

checks = {
    "send_total_exact": len(message_ids) == expected_total,
    "send_errors_zero": len(send_errors) == 0,
    "api_status_sent_all": status_counts.get("sent", 0) == expected_total,
    "agent_reply_exists": chat_counts.get(("AGENT_REPLY", "sent"), 0) >= 1,
    "single_runtime": runtime_count == 1,
    "runtime_rest_success": tool_per_name["runtime_rest"]["success_false"] == 0 and tool_per_name["runtime_rest"]["success_true"] >= 1,
    "chat_reply_success": tool_per_name["chat_reply"]["success_false"] == 0 and tool_per_name["chat_reply"]["success_true"] >= 1,
    "no_trs_connection_refused_logs": forbidden_hits["trs_connection_refused"] == 0,
    "no_ro_internal_messages_404": forbidden_hits["ro_internal_messages_404"] == 0,
}

passed = all(checks.values())
report = {
    "passed": passed,
    "checks": checks,
    "config": {
        "rate_per_second": RATE_PER_SECOND,
        "duration_seconds": DURATION_SECONDS,
        "drain_seconds": DRAIN_SECONDS,
        "expected_total": expected_total,
    },
    "metrics": {
        "agent_id": agent_id,
        "start_iso": start_iso,
        "sent_total": len(message_ids),
        "send_errors": len(send_errors),
        "avg_send_ms": round(sum(lat_ms) / len(lat_ms), 2) if lat_ms else None,
        "api_status_counts": dict(status_counts),
        "chat_breakdown": chat_breakdown,
        "task_breakdown": task_breakdown,
        "saga_breakdown": saga_breakdown,
        "tool_execute_by_name": tool_per_name,
        "runtime_count": runtime_count,
        "forbidden_hits": forbidden_hits,
    },
    "send_error_samples": send_errors[:10],
}

out = pathlib.Path(DATA_DIR) / "health_gate_report.json"
out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(str(out))
print(json.dumps({"passed": passed, "checks": checks}, ensure_ascii=False))
sys.exit(0 if passed else 2)
PY
PY_EXIT=$?
set -e

REPORT_FILE="$(${PYTHON_CMD} - <<PY
import pathlib
p = pathlib.Path("${REPORT_STDOUT_FILE}")
line = ""
if p.exists():
    lines = [x.strip() for x in p.read_text(encoding="utf-8", errors="ignore").splitlines() if x.strip()]
    if lines:
        line = lines[0]
print(line)
PY
)"

if [[ -f "${REPORT_STDOUT_FILE}" ]]; then
  echo "[health-gate] python-summary:"
  ${PYTHON_CMD} - <<PY
import pathlib
p = pathlib.Path("${REPORT_STDOUT_FILE}")
if p.exists():
    lines = [x.rstrip() for x in p.read_text(encoding="utf-8", errors="ignore").splitlines() if x.strip()]
    if len(lines) > 1:
        print(lines[1])
PY
fi

echo "[health-gate] report=${REPORT_FILE}"
if [[ "${PY_EXIT}" -eq 0 ]]; then
  echo "[health-gate] PASS"
else
  echo "[health-gate] FAIL"
  exit "${PY_EXIT}"
fi
