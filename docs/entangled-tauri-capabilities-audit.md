# Tauri 能力与敏感 command 审计（E.2 占位）

> 当前仓库 Tauri 配置以 `novaic-app/src-tauri/tauri.conf.json`（v2 schema）为主；**未**使用独立 `capabilities/*.toml` 目录。本文件记录审计方法与待办勾选。

## 敏感面（建议清单）

以下 `invoke` 应 **仅** 出现在受信壳（本机 Tauri WebView）路径，不应暴露给不可信远程 WebView（OTA 全页加载策略下尤需核对）：

- `entangled_*` / `entity_*`：直连本地 SQLite / 同步。
- 任意写文件、执行 shell、VM 控制、凭据类 command。

## 审计步骤

1. 在 `novaic-app/src` 全文检索 `invoke(`，导出 **command 名称列表**。
2. 在 `src-tauri/src` 检索 `#[tauri::command]` / `generate_handler!`，与前端列表 **求交集**。
3. 将「高敏感」command 记入下表，并确认 OTA 加载页未注册或二次校验。

## 勾选表（人工）

| Command / 能力 | 风险 | OTA 是否允许 | 备注 |
|----------------|------|----------------|------|
| （待填） | | | |

## 参考

- Tauri 2 security: app `security` 与 plugin allowlist（见官方文档）。
- 与 [entangled-push-to-all-audit.md](./entangled-push-to-all-audit.md) 交叉：服务端广播与客户端 invoke 是不同平面，需分别审计。
