# 本地开发（Runbook）

与根目录 **`HANDOVER.md` §四** 对齐；此处为精简可执行清单。

## 环境

- Node ≥ 18、npm ≥ 9  
- `rustup` + stable `cargo`  
- macOS：`xcode-select --install`

## 只跑前端（无 Tauri）

```bash
cd novaic-app
npm install
npm run dev
```

浏览器：`http://localhost:5173`

## 完整桌面（含 Rust / VmControl）

```bash
cd novaic-app
npm install
npm run tauri:dev
```

## 常见问题

- **端口 1420 被占用**：`kill $(lsof -ti:1420)`（见 `HANDOVER.md`）
- **构建桌面 release**：不要用 `npm run tauri build --ci`；使用 `npm run tauri:build -- --bundles app`（见 `HANDOVER.md`）

## 相关服务

本地若需 Gateway、Cortex、Agent-Runtime 等，请查阅对应 submodule 的 README 与 `novaic-common/config/services.json` 中的端口；架构关系见 **`docs/architecture/overview.md`**。
