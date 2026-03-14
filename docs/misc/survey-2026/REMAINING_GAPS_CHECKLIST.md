# 剩余缺口修复 Checklist

> 基于 `CURRENT_STATE_SURVEY_SUMMARY_2026.md` 三、剩余缺口汇总表  
> 创建日期：2026-03-12

---

## 已修复（2026-03-12 前）

| 缺口 | 状态 |
|------|------|
| E1 invoke 失败无 .catch | ✅ 已修复 |
| App Instance 双重异步 | ✅ 已修复（resolveCurrentPcClientId 重试） |
| useAgentDevice 多 PC 缓存 | ✅ 已修复 |
| statusKey 抽离共享 util | ✅ 已修复 |
| DeviceManagerPage deviceMode | ✅ 已修复 |

---

## 待修复清单

### P1（高优先级）

| # | 缺口 | 描述 | 位置 | 状态 |
|---|------|------|------|------|
| 1 | listForUser status 缓存 | 后端 listForUser 的 status 来源与缓存策略审查 | novaic-gateway | ⬜ 待办 |

### P2（中优先级）

| # | 缺口 | 描述 | 位置 | 状态 |
|---|------|------|------|------|
| 2 | 错误提示区分 | resolveCurrentPcClientId 失败时区分根因 | novaic-app | ✅ 已修复 |
| 3 | 30s 可能不足 | 远端+subuser 场景 WS_UPGRADE_TIMEOUT 延长至 60s | novaic-app src-tauri | ✅ 已修复 |
| 4 | vm/start 多 PC | Gateway vm/start 增加 pc_client_id | novaic-gateway | ✅ 已修复 |
| 5 | R3 余量 | Relay 20s→25s 极端慢网 | novaic-gateway / relay | ✅ 已修复 |
| 6 | E4 PC relay 失败反馈 | PC relay 失败时向手机反馈 | 需架构设计 | ⬜ 待办 |
| 7 | ensure_vnc_endpoint 错误传播 | PC 侧 subuser 超时错误通过 QUIC 传回 | novaic-app src-tauri | ⬜ 待办 |

### P3（低优先级）

| # | 缺口 | 描述 | 位置 | 状态 |
|---|------|------|------|------|
| 8 | 错误文案中英混用 | VNC 相关文案统一为中文 | novaic-app | ✅ 已修复 |
| 9 | 并发 relay_request | 2s 内同 target 复用 session | novaic-gateway | ⬜ 待办 |

---

## 实施进度

- [x] P2-2 错误提示区分
- [x] P3-8 错误文案统一
- [x] P2-3 VNC 30s→60s
- [x] P2-4 vm/start pc_client_id
- [x] P2-5 R3 余量 25s
- [ ] P1-1 listForUser 缓存审查
- [ ] P2-6 E4 PC relay 失败反馈
- [ ] P2-7 ensure_vnc_endpoint 错误传播
- [ ] P3-9 并发 relay_request 去重
