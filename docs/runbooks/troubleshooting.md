# 故障排查手册

## 服务启动失败

| 症状 | 可能原因 | 排查步骤 |
|------|----------|----------|
| 端口已被占用 | 上次进程未正常退出 | `lsof -i:<port>` 找到占用进程，`kill` 后重启 |
| ServiceConfig 加载失败 | services.json 缺失或格式错误 | 检查 `novaic-common/config/services.json` 是否存在且 JSON 合法 |
| Redis 连接失败 | Redis 未启动 | `redis-cli ping` 确认 Redis 运行；Cortex 依赖 Redis |
| Python 模块找不到 | venv 未激活或依赖未安装 | `source .venv/bin/activate && pip install -e .` |
| SQLite 锁定 | 数据库文件被其他进程锁定 | 停止所有相关进程后重启 |

## 连接问题

### Gateway 不可达

1. 确认 Gateway 在 :19999 运行：`curl http://127.0.0.1:19999/api/health`
2. 检查 Nginx 配置（生产环境）：`nginx -t && systemctl status nginx`
3. 检查 JWT 认证：确认请求携带有效 token

### AppBridge WebSocket 断连

1. 检查 Gateway 日志中的 WS 错误
2. 确认客户端 JWT 未过期
3. 检查网络连通性和防火墙规则
4. AppBridge 心跳间隔 30s，超时 90s 自动重连

### Entangled 同步异常

1. 确认 Entangled 服务在 :19900 运行
2. 检查 `entangled_auth_rejected` 事件（JWT 问题）
3. 客户端重置缓存：Tauri 命令 `entangled_cache_reset`
4. 检查 schema push 是否完成：`entangled_wait_schema`

## Agent 执行异常

### Worker 无响应

1. 检查 Queue Service :19997 状态
2. 查看 worker 进程是否存活
3. 检查 worker 日志中的错误
4. 确认依赖服务（Cortex、LLM Factory、Device）可达

### LLM 调用失败

1. 检查 LLM Factory :9100 状态
2. 确认 API Key 已配置且有效
3. 检查 Provider 响应错误（429 限流、401 认证、500 服务端错误）
4. LLM Factory 有指数退避重试，等待后重试

### 工具执行失败

1. **Sandbox 执行失败**：检查 Sandbox Service :19994，确认 mount namespace 权限
2. **设备工具失败**：检查 Device :19993 → VmControl 连接，确认 Cloud Bridge WS 存活
3. **MCP-VMUSE 失败**：确认 VM 内 :8080 服务运行，检查 QEMU 端口转发

## WebRTC 连接失败

| 阶段 | 排查 |
|------|------|
| 信令失败 | 检查 AppBridge WS 连接，确认 Gateway 信令转发正常 |
| ICE 失败 | 检查 TURN 服务器配置，确认 UDP 端口可达 |
| 视频黑屏 | 检查 VmControl VideoBroadcaster 日志，确认编码器启动 |
| 输入无响应 | 检查 DataChannel 状态，确认输入适配器匹配设备类型 |
| Scrcpy 连接超时 | ADB forward 端口是否可达，scrcpy-server 是否启动（最多重试 15 次，约 12s） |

## 日志位置

### 本地开发

各服务日志输出到 stdout/stderr。

### 生产环境

| 服务 | 日志路径 |
|------|----------|
| Gateway | `/opt/novaic/data/logs/gateway-$(date +%Y%m%d).log` |
| Queue Service | `/opt/novaic/data/logs/queue-service.log` |
| Sandbox | `/opt/novaic/data/logs/sandboxd.log` |
| Agent Runtime | `/opt/novaic/data/logs/runtime_logs/` |
| 其他服务 | `/opt/novaic/data/logs/<service>.log` |

### 查看日志

```bash
# 实时跟踪 Gateway 日志
tail -f /opt/novaic/data/logs/gateway-$(date +%Y%m%d).log

# 搜索 AppBridge WS 日志
grep -E 'AppWS|WebSocket' /opt/novaic/data/logs/gateway-*.log

# 查看 worker 状态
python3 /opt/novaic/services/novaic-agent-runtime/runtime_worker_roster.py
```

## 恢复步骤

### 全服务重启（生产）

```bash
ssh root@api.gradievo.com
/opt/novaic/start.sh
```

所有重启应通过 `start.sh`，不要单独重启 Gateway（易导致状态不一致）。

### 清理 Agent 状态

如果 Agent 执行卡住，可通过 Business API 或 Queue Service API 取消任务。

### Entangled 缓存重置

客户端执行 `entangled_cache_reset` Tauri 命令，清空本地 SQLite 缓存并重新订阅。
