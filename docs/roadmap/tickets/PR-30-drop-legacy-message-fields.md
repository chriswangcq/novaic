# PR-30  删除 `chat_messages` 旧状态字段

| 字段 | 值 |
| --- | --- |
| **Phase** | 5 |
| **Milestone** | M4 |
| **承诺** | R4 + R8 |
| **Status** | `[ ]` |
| **Depends on** | PR-21, PR-22, PR-23（稳定 ≥ 1 release） |
| **Blocks** | — |
| **估时** | 0.5 d |
| **Owner** | __ |
| **PR 标题** | `refactor(entangled): drop chat_messages legacy fields (processed/read/claimed_by/claimed_at/status)` |

## 目标

在 `lifecycle` 字段稳定运行 ≥ 1 个 release 后，彻底删旧字段，结束"双字段维护"成本。

## 范围

- Entangled schema `chat_messages.json`
- 所有读旧字段的代码路径
- 迁移脚本（sqlite `ALTER TABLE ... DROP COLUMN`，需要 3.35+）

## 前置 Checklist

- [ ] PR-21 / PR-22 / PR-23 稳定运行 ≥ 1 release（建议 2 周以上）
- [ ] `rg 'processed|read|claimed_by|claimed_at|\.status' novaic-*/ | rg 'chat_messages' | rg -v 'lifecycle|tests|migrations'` 清点
- [ ] **生产 DB 备份**

## 实施 Checklist

### 1. 代码清理

- [ ] 所有读 `processed` / `read` / `claimed_by` / `claimed_at` / `status`（对 chat_messages）的代码改读 `lifecycle` / `claimed_by_scope`
- [ ] 删除向旧字段写的所有代码
- [ ] 删除读旧字段的 API 响应体字段（或保留只读兼容一个 release）

### 2. Schema 变更

- [ ] sqlite 3.35+ 支持 `ALTER TABLE ... DROP COLUMN`：
  ```sql
  ALTER TABLE chat_messages DROP COLUMN processed;
  ALTER TABLE chat_messages DROP COLUMN read;
  ALTER TABLE chat_messages DROP COLUMN claimed_by;
  ALTER TABLE chat_messages DROP COLUMN claimed_at;
  ALTER TABLE chat_messages DROP COLUMN status;
  ```
- [ ] 若 sqlite < 3.35 → 必须用 "CREATE NEW TABLE + INSERT SELECT + DROP + RENAME" 的五步法
- [ ] Schema 版本号 +1

### 3. 观察窗

- [ ] 合并后观察 24h：无 `column not found` / 字段 KeyError

## 测试 Checklist

- [ ] 单测：所有读/写 `lifecycle` 的代码继续工作
- [ ] 集成：发消息 → 生命周期完整
- [ ] 迁移脚本在一份 snapshot DB 上跑 → 剩余字段正确

## 可观测性 Checklist

- n/a（仅清理）

## 文档 Checklist

- [ ] [message-wake-refactor.md](../message-wake-refactor.md) P5-4 → `[x]`
- [ ] 本工单 Status → `[x]`
- [ ] [architecture/entity-data-models.md](../../architecture/entity-data-models.md) 删除旧字段条目

## 验收命令

```bash
sqlite3 ~/.novaic/data/entangled.db "PRAGMA table_info(chat_messages);"
# 不再包含 processed/read/claimed_by/claimed_at/status

rg '\.processed|\.claimed_by\W' novaic-*/ | rg -v lifecycle | rg -v 'tests/|migrations/'
# 预期：空
```

## 回滚

- **危险**：DROP COLUMN 不可逆。若需要回滚：
  1. 从生产 DB 备份恢复
  2. revert 代码

## 备注

- 一定要等 ≥ 1 release 稳定再做；过早会让老客户端 / 老代码崩溃。
- 本 PR 应在周初合并 + 当周密切观察。
