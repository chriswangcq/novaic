# 常见问题与排障

> 与当前实现/已修复问题一致；对应原 **`HANDOVER.md` §十五**。新现象请查 Gateway、task-worker、AppBridge 日志。

## 问题速查表

| 问题 | 原因 | 解决 |
|------|------|------|
| **AppBridge 秒断 / `WS not connected (action=entity)`** | Gateway `/api/app/ws` handler 异常（客户端 RST）；曾见 `exists_before` → `KeyError: 'rowid'` | 部署 `store.py` 游标 **`AS _cf, AS _rid`**；`grep Message loop crashed gateway-*.log`，对齐 `[AppWS] accepted` / `handler exiting` |
| macOS SIGTRAP | enigo 键盘须在 main queue | 已改 CGEvent |
| **Entangled WS Message too long** | head_n 未 LIMIT，全量过大 | Gateway/Entangled 透传 `limit` |
| **UI 冻结 / Device tab 卡死** | `getCachedUser()` 每次新对象 → useEffect 死循环 | 依赖改为 **userId 字符串** |
| **宽屏消息不可见** | opacity-0 + `h-full` 高度为 0 | `flex-1 min-h-0` |
| Gateway 无响应 | WAL/SHM 损坏 | 停服务后删 `*.db-wal` / `*.db-shm`（谨慎） |
| Gateway 500 | `JWT_SECRET` 未设置 | 检查 `jwt_secret.env` |
| Gateway 写锁 | 写未在 transaction | `with db.transaction("global")` |
| Port **1420** 占用 | 上次 dev 未退出 | `kill $(lsof -ti:1420)` |
| App 一直 Connecting | pushToken 顺序 | 先 `await pushToken()` 再 initialize |
| Rust panic Cannot block | async 里 `blocking_read` | `read().await` |
| iOS 黑屏 | custom-protocol + WKWebView | 构建 `--features mobile` |
| `tauri ios run` 失败 | exportOptionsPlist | build + devicectl install |
| iOS arch 错 | FORCE_COLOR | `patch-ios-xcode.sh` |
| iOS aws-lc-sys | Xcode beta SDKROOT | 正式版 Xcode |
| LLM 429 / 超时 | 限流/过载 | task-worker 日志、退避 |
| 截图截错屏 | runtime_context 缺 display | 注入 display |
| scrcpy 无响应 | TCP 断未 break | write 失败 break |
| WebRTC 多端互踢 | stop_peers 等 | 见历史修复 |
| coturn 新连接失败 | 僵尸 session | 重启 coturn |
| Relay handshake timeout | open_bi | accept_bi |
| **agent-binding 保存后消失** | update 无行；nav 未订阅 agent-binding | upsert；nav 增加订阅；settings 传 agentId |
| **绑定 UI 与缓存不一致** | RQ stale、entity_get | `createFormStore` upsert 成功处理；`allowMissing` |
| **选无设备仍绑定** | `currentBinding` 被清空 | `bindingData?.device_id` 触发 clear |
| **执行日志条偏右** | Framer `transform` | `ChatPanel` flex 居中 + `px-4` |
| **device 浮窗不显示** | 读错数据源 | `agentBindingStore.useForm()` |
| **sync_contract_version 为 0** | schema 首包缺字段 | `app_client.py` 与 TS 解析 `{ entities, syncContractVersion }` |
| **选 Agent 状态异常** | `useCallback` 闭包 | `handleSelectAgent` / `handleAgentCreated` 依赖 **`agents`** |
| **登出仍弹设置** | `settingsOpen` | `handleLogout` 置 **`settingsOpen: false`** |
| **`PRAGMA wal_checkpoint(TRUNCATE)`** | 截断未提交事务 | **禁止运行时执行** |

## LLM 调用失败排查

1. 日志：`grep -E "429|think.*failed" /opt/novaic/data/logs/task-worker-*.log`
2. Context：从 **`tq_sagas.step_results`** 等与 `read_context` 相关字段取（**不要**误用 `runtime.context`）
3. 重放：`POST /api/queue/tasks/publish` topic=`llm.call`
4. 脚本：`novaic-agent-runtime/scripts/trace_llm_call.py`（若存在）

## 相关

- [../architecture/entangled-store-and-app-ws.md](../architecture/entangled-store-and-app-ws.md) — AppWS / store  
- [../reference/config-and-environment.md](../reference/config-and-environment.md)  
