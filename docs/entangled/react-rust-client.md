# Rust Rust Client 与 Path C 架构

> 路径参考：`Entangled/packages/client-rust/` 与 `novaic-app/src/data/entangled/`

## 1. IndexedDB 时代的落幕
在早期的 Path B，大量的同步数据由前端自行处理并存入浏览器主线程的 IndexedDB（例如 Dexie），这导致了不可调和的问题：
- Safari / 移动端 WKWebView 内 IndexedDB 失效与吞吐瓶颈；
- 标签页面多次打开与 WebWorkers 通信的数据“双读双写”极易崩溃；
- 大列表 `render` 经常锁死 React Fiber 甚至造成 React 整个树雪崩。

## 2. Headless Client (Tauri Sqlx 代理)
在全新的 **Path C**，客户端转变为完全 **Headless 核心 + React 壳** 的模式：
- **核心数据存入本地 SQLite (`entangled_cache.db`)**：
    所有来自于云端的历史全量和增量 Patch 都在 `client-rust/src/push.rs` 中被解析，并用 Rust 侧内建的 SQLite 以 `sqlx` 同步。
- **由后端驱动前端（事件驱动）**：
    数据落盘之后，Rust 从 SQLite 返回更新状态的摘要，向前端 Tauri 频道发射 `entities_changed`。事件中会带上精准的 `params`。
- **完全解耦 React Hooks**：
    React 从之前沉重的请求协调者，变成纯展示层。通过简单的工厂函数 (`createListStore`, `createFormStore`) 以及 `staleTime: Infinity`，前端不再轮询，仅随事件来改变状态。

## 3. Clear Cache 与清理机制
- 浏览器提供的 `Clear Cache` 并不能触达 Rust 中的文件持久层；
- 现在，点击重置会导致发起 Command `entity_cache_clear`。
- Rust 将从表映射表 `sqlite_master` 之中粗暴地发起对每个有业务含义全量 `user` 的表执行 `DELETE`；随之自动对文件做 `VACUUM` 压缩。这避免了卸载重装 App 以后仍然残存陈旧实体 ID 的历史债务。

当前客户端 cache 是 read-model，不是离线写队列。正常表结构：

```text
entity_meta
entity_items
idx_entity_items_seq
```

历史 `pending_ops` 已退役；Rust 初始化会清掉遗留表。执行日志的长结果不进入 `entangled_cache.db` 热 row：`execution-logs` 只保留轻量 metadata，`log-payloads` 通过 action lazy fetch，工具长结果在 Cortex step，原始 LLM 调用在 LLM Factory。

排障：

```bash
sqlite3 "$HOME/Library/Application Support/com.novaic.app/entangled_cache.db" ".tables"
```
