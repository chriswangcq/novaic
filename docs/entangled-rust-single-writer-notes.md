# Rust 单写者 Cache Worker（B.4 设计笔记）

> **未在本分支实现完整单写者**；以下为落地时建议结构，便于后续 PR。

## 动机

当前 `process_sync` 经 `spawn_blocking` 进入线程池：实现简单，高 QPS 下有调度开销。单写者线程 **串行** 持有 `Cache` + 连接池，可去掉 per-frame 线程池税。

## 约束

- **单线程**写 SQLite + `Cache`；其他线程只通过 `mpsc` 投递 `SyncFrame`。
- 与现有 **有界队列 + try_send 背压** 兼容；worker 退出与 sender drop 行为保持不变。
- 超时 / 慢帧日志沿用 `process_ms` 与 `entity` 字段。

## 迁移步骤（建议）

1. 在 `app_bridge` 中引入 `std::thread::spawn` + `crossbeam_channel`（或保留 `tokio::mpsc` + `block_in_place` 单任务），**禁止** worker 内再 `spawn_blocking` 写同一 `Cache`。
2. 压测对比 P95（见 [entangled-load-test.md](./entangled-load-test.md)）。
3. 保留特性开关：异常时回退当前 `spawn_blocking` 路径。

## 风险

- 死锁：确保 worker 不 `await`、不持有 async 锁跨 `.await`。
- 与 heartbeat 交错：保留现有 `select!` 语义。
