# 常见问题与排障

> 摘自 `**HANDOVER.md` §十五**。新现象请先查 **Gateway / task-worker 日志** 与本文未覆盖时回看 HANDOVER 全文。

## 速查表


| 问题                                                    | 原因                                                                           | 处理                                                                                     |
| ----------------------------------------------------- | ---------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| **AppBridge 秒断 / `WS not connected (action=entity)`** | 多为 Gateway `/api/app/ws` handler 异常；曾见 `exists_before` → `KeyError: 'rowid'` | 查 `store.py` 游标别名 `**_cf`/`_rid**` 是否已部署；服务器 `grep Message loop crashed gateway-*.log` |
| macOS SIGTRAP                                         | enigo 键盘须在 main queue                                                        | 已改 CGEvent（见 architecture/thin-client-and-topology）                                    |
| **Entangled WS Message too long**                     | head_n 未 limit 全量过大                                                          | Gateway/Entangled 透传 `limit`                                                           |
| **UI 冻结 / Device tab 卡死**                             | `getCachedUser()` 每次新对象 → useEffect 死循环                                      | 依赖改为 **userId 字符串**                                                                    |
| **宽屏消息不可见**                                           | opacity-0 + `h-full` 高度为 0                                                   | `flex-1 min-h-0` 等                                                                     |
| Gateway 无响应                                           | WAL/SHM 损坏                                                                   | 停服务后删 `*.db-wal`/`*.db-shm` 谨慎操作                                                       |
| Gateway 500                                           | `JWT_SECRET` 未配置                                                             | 检查 `jwt_secret.env`                                                                    |
| Gateway 写锁                                            | 写未进 transaction                                                              | `with db.transaction("global")`                                                        |
| Port **1420** 占用                                      | 上次 dev 未退出                                                                   | `kill $(lsof -ti:1420)`                                                                |
| App 一直 Connecting                                     | pushToken 顺序                                                                 | 先 `await pushToken()` 再 initialize                                                     |
| Rust panic Cannot block                               | async 里 blocking_read                                                        | 用 `read().await`                                                                       |
| iOS 黑屏                                                | custom-protocol + WKWebView                                                  | 构建用 `--features mobile`                                                                |
| `tauri ios run` 失败                                    | exportOptionsPlist 路径                                                        | build + devicectl install                                                              |
| iOS arch 错                                            | FORCE_COLOR 当 arch                                                           | `patch-ios-xcode.sh`                                                                   |
| iOS aws-lc-sys 失败                                     | Xcode beta SDKROOT                                                           | 用正式版 Xcode                                                                             |
| LLM 429/超时                                            | 限流/过载                                                                        | 查 task-worker 日志、退避                                                                    |
| scrcpy 无响应                                            | 控制 TCP 断未 break                                                              | 已修：write 失败 break                                                                      |
| WebRTC 多端互踢                                           | stop_peers 等                                                                 | 见 HANDOVER 历史修复                                                                        |
| coturn 新连接失败                                          | 僵尸 session                                                                   | 重启 coturn                                                                              |
| **agent-binding 保存后消失**                               | update 无行；nav 未订阅                                                            | upsert；nav 增加 **agent-binding**                                                        |
| **sync_contract_version 为 0**                         | schema 首包缺版本                                                                 | 查 AppWS 与 TS 解析                                                                        |
| **登出仍弹设置**                                            | `settingsOpen` 未清                                                            | `handleLogout` 置 `settingsOpen: false`                                                 |


**禁止**：运行时执行 `**PRAGMA wal_checkpoint(TRUNCATE)`**。

## LLM 调用失败（摘要）

1. 日志：`grep -E "429|think.*failed" .../task-worker-*.log`
2. Context：从 saga step_results 等取（不要用错表）
3. 重放 / trace：见 `novaic-agent-runtime/scripts/trace_llm_call.py`（若存在）

## 相关

- [../architecture/realtime-sync.md](../architecture/realtime-sync.md) — WS / Entangled  
- [../reference/config-and-environment.md](../reference/config-and-environment.md) — 路径与 env