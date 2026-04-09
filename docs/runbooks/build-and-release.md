# 构建与发布（客户端）

> 对应 **`HANDOVER.md` §五**。命令以 **`novaic-app/package.json`** 为准。

## 环境

- Node ≥ 18、npm ≥ 9；Rust stable；macOS 需 Xcode 工具链。

## 桌面

```bash
cd novaic-app
npm install
npm run tauri:build -- --bundles app
# 产物：src-tauri/target/release/bundle/macos/（App 名以仓库为准）
```

勿用 `npm run tauri build --ci`（见 HANDOVER）。

## iOS（摘要）

- 一键：`./scripts/build-and-install-ios.sh`（若存在）。
- **`tauri ios run`** 因 exportOptionsPlist 等问题可能失败；常用 **build + devicectl install**。
- 黑屏：构建 feature 用 **`mobile`**；`VITE_GATEWAY_URL` 兜底、`tauri.ios.conf.json` 覆盖桌面配置等 — 见 HANDOVER §5.2。
- Xcode 26 beta 与 `aws-lc-sys` 交叉编译问题：优先正式版 Xcode。

## Android

```bash
npm run tauri:build:android
```

（与 iOS 的 protocol/feature 组合可能不同，见 HANDOVER。）

## OTA 前端

生产部署见 [**`deploy.md`**](deploy.md) 与 [**`cloud-production.md`**](cloud-production.md)（CDN 域名三处同步：`config/index.ts`、`remote-frontend.json`、`setup.rs`；脚本 `scripts/check-ota-sync.sh`）。
