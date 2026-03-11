# 端到端测试就绪说明

> 基于 Phase 1–4 优化后的状态。Build 已验证通过。

## 一、Build 状态

```bash
./build-all.sh
```

**结果**：6 个二进制已生成到 `dist/`：

| 二进制 | 说明 |
|--------|------|
| novaic-storage-a | File Service |
| novaic-storage-b | Tool Result Service |
| novaic-runtime-orchestrator | RO 内部 API |
| novaic-gateway | Gateway REST API |
| novaic-tools-server | 工具服务 |
| novaic-agent-runtime | Queue Service + Watchdog + Task/Saga/Health Workers |

## 二、E2E 启动顺序

```bash
DATA_DIR="${NOVAIC_DATA_DIR:-$HOME/.novaic}"
mkdir -p "$DATA_DIR"
DIST="./dist"

# 1. Storage A
$DIST/novaic-storage-a --port 19995 --data-dir "$DATA_DIR" &

# 2. Storage B
$DIST/novaic-storage-b --port 19994 --data-dir "$DATA_DIR" \
  --file-service-url http://127.0.0.1:19995 \
  --gateway-url http://127.0.0.1:19999 &

# 3. Runtime Orchestrator
$DIST/novaic-runtime-orchestrator --port 19993 --data-dir "$DATA_DIR" &

# 4. Queue Service（从 agent-runtime）
$DIST/novaic-agent-runtime queue-service --host 127.0.0.1 --port 19997 --data-dir "$DATA_DIR" &

# 5. Gateway（需等 RO、Queue 就绪）
$DIST/novaic-gateway --port 19999 --data-dir "$DATA_DIR" \
  --runtime-orchestrator-url http://127.0.0.1:19993 \
  --queue-service-url http://127.0.0.1:19997 \
  --tools-server-url http://127.0.0.1:19998 \
  --vmcontrol-url http://127.0.0.1:19996 \
  --file-service-url http://127.0.0.1:19995 \
  --tool-result-service-url http://127.0.0.1:19994 &

# 6. Tools Server
$DIST/novaic-tools-server --port 19998 --gateway-url http://127.0.0.1:19999 &

# 7. Workers（watchdog、task-worker、saga-worker、health）
$DIST/novaic-agent-runtime watchdog --gateway-url http://127.0.0.1:19999 \
  --queue-service-url http://127.0.0.1:19997 \
  --runtime-orchestrator-url http://127.0.0.1:19993 \
  --data-dir "$DATA_DIR" &

$DIST/novaic-agent-runtime task-worker --gateway-url http://127.0.0.1:19999 \
  --queue-service-url http://127.0.0.1:19997 \
  --tools-server-url http://127.0.0.1:19998 \
  --runtime-orchestrator-url http://127.0.0.1:19993 \
  --tool-result-service-url http://127.0.0.1:19994 \
  --data-dir "$DATA_DIR" &

$DIST/novaic-agent-runtime saga-worker --gateway-url http://127.0.0.1:19999 \
  --queue-service-url http://127.0.0.1:19997 \
  --runtime-orchestrator-url http://127.0.0.1:19993 \
  --data-dir "$DATA_DIR" &

$DIST/novaic-agent-runtime health --gateway-url http://127.0.0.1:19999 \
  --queue-service-url http://127.0.0.1:19997 \
  --runtime-orchestrator-url http://127.0.0.1:19993 \
  --data-dir "$DATA_DIR" &
```

**注意**：需有 vmcontrol 服务在 19996 端口，否则 Gateway 启动可能失败。若无 vmcontrol，可临时用占位 URL（如 `http://127.0.0.1:19996`），部分功能可能不可用。

## 三、健康检查

```bash
curl -s http://127.0.0.1:19999/api/health   # Gateway
curl -s http://127.0.0.1:19993/api/health   # RO
curl -s http://127.0.0.1:19999/api/health   # Gateway
curl -s http://127.0.0.1:19998/api/health   # Tools Server
curl -s http://127.0.0.1:19997/api/health   # Queue Service
curl -s http://127.0.0.1:19995/api/health   # Storage A
curl -s http://127.0.0.1:19994/api/health   # Storage B
```

## 四、参考文档

- `novaic/dev-guide/smoke-test.md` – 冒烟测试流程
- `novaic-gateway/scripts/smoke_gateway_repo_root.sh` – Gateway 独立冒烟测试
- `novaic-control-plane/rounds/round-004/20-reports/run_storage_ab_cross_repo_e2e_round004.sh` – Storage A/B 跨 repo E2E
