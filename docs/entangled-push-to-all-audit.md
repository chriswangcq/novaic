# `push_to_all` 调用审计（E.3）

> 设计文档要求审计「广播到所有 App WS」能力，避免不可信上下文误用。

## 结论（2026-04-01）

| 符号 | 路径 | 调用方（仓库内） |
|------|------|------------------|
| `push_to_all` | `novaic-gateway/gateway/api/app_client.py` | **无**（仅定义，未发现 `push_to_all(` 引用） |

## 相关能力

- **`notify_all`（Entangled notifier）**：向所有已注册 `push_fn` 的客户端广播；与 Gateway `push_to_user` 不同，需注意多用户隔离（见 [entangled-multi-worker-threat-model.md](./entangled-multi-worker-threat-model.md)）。
- **`push_to_user`**：按 `user_id` 定向推送 — 业务路径应优先使用此接口。

## 建议

- 若未来引入 `push_to_all` 调用，在 PR 中注明 **事件类型、数据来源、是否含 PII**，并默认走 `push_to_user`。
- OTA / 不可信 WebView 不得获得能触发服务端广播的凭据（见 capabilities 审计文档）。
