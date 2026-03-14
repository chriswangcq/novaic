# Phase 4 测试审查报告 — 4 名测试工程师

> 挑刺式审查，接受客观意见并修复。

---

## 测试工程师 1：逻辑与边界

| 问题 | 严重度 | 描述 |
|------|--------|------|
| relay_url_override 空串 | 中 | `relay_url_override: Some("")` 会传入 `parse_relay_url` 导致失败，应视为 `None` |
| 无 | - | RelayOnly 提前返回，discovery=None 时正确走 punch_or_relay ✓ |
| 无 | - | DirectOnly + discovery=None 正确 bail ✓ |

---

## 测试工程师 2：API 与契约

| 问题 | 严重度 | 描述 |
|------|--------|------|
| client 模块注释过时 | 低 | "当前仅实现 ConnectStrategy::DirectOnly" 已不成立 |
| Relay 分支冗余 | 低 | `matches!` + `if let` 可简化为单次 `if let` |
| RelayRole 缺 Debug | 低 | 错误/日志中难以区分 Pc/Mobile |

---

## 测试工程师 3：健壮性与安全

| 问题 | 严重度 | 描述 |
|------|--------|------|
| relay_url_override 空串 | 中 | 同上，需在 punch_or_relay 内过滤 |
| NOVAIC_RELAY_URL 未文档化 | 低 | 配置读取环境变量但无说明 |

---

## 测试工程师 4：文档与一致性

| 问题 | 严重度 | 描述 |
|------|--------|------|
| client 模块注释过时 | 低 | 同上 |
| PHASE4 一、当前状态 | 低 | 仍写「在 hole_punch.rs」，应改为 relay.rs |
| config 无 NOVAIC_RELAY_URL 说明 | 低 | 应在 config 或文档中说明 |

---

## 修复清单

- [x] relay_url_override 空串视为 None
- [x] 更新 client 模块注释
- [x] 简化 Relay 端点 match
- [x] RelayRole 增加 Debug
- [x] config 增加 NOVAIC_RELAY_URL 文档
- [x] 更新 PHASE4-TASK-BREAKDOWN 当前状态
